#!/command/with-contenv bashio
# ==============================================================================
# Home Assistant Community App: CybroScgiServer
# Pre-run checks for CybroScgiServer
# ==============================================================================
declare configuration_file
declare ha_config_file
declare autodetect_address
declare push_enabled
declare verbose_level

crudini="crudini"

configuration_file=$(bashio::config 'configuration_file')
# copy config from legacy config folder to app config folder
ha_config_file="${configuration_file/"/config"/"/homeassistant"}"
if bashio::fs.file_exists "${ha_config_file}"; then
    bashio::log.warning "Found app config in:"
    bashio::log.warning "${ha_config_file}"
    bashio::log.warning
    bashio::log.warning "move config into app config folder:"
    bashio::log.warning "${configuration_file}"
    mv "${ha_config_file}" "${configuration_file}"
fi
# Creates initial CybroScgiServer configuration in case it is non-existing
if ! bashio::fs.file_exists "${configuration_file}"; then
    cp /usr/local/bin/scgi_server/config.ini "$(bashio::config 'configuration_file')" 
    bashio::log.fatal
    bashio::log.fatal "Seems like the configured configuration file does"
    bashio::log.fatal "not exists:"
    bashio::log.fatal
    bashio::log.fatal "${configuration_file}"
    bashio::log.fatal
    bashio::log.fatal "A default configuration file is created!"
    bashio::log.fatal "Please add your controller at the end."
    bashio::log.fatal
    bashio::exit.nok
else
    bashio::log.info "Using existing configuration file: ${configuration_file}, and applying the following settings:"
    cp "$(bashio::config 'configuration_file')" /usr/local/bin/scgi_server/config.ini

    # ethernet settings
    # controllers send push messages to port 8442, so don't use a dynamic port
    if [[ -z "$($crudini --get /usr/local/bin/scgi_server/config.ini ETH port 2>/dev/null)" ]]; then
        bashio::log.info "ETH port not set, using 8442"
        $crudini --set /usr/local/bin/scgi_server/config.ini ETH port 8442
    fi
    $crudini --set /usr/local/bin/scgi_server/config.ini ETH autodetect_enabled true
    if bashio::config.has_value "autodetect_address"; then autodetect_address=$(bashio::config 'autodetect_address'); else autodetect_address=""; fi
    bashio::log.info "autodetect_address: ${autodetect_address}"
    $crudini --set /usr/local/bin/scgi_server/config.ini ETH autodetect_address "$autodetect_address"

    # push settings
    if bashio::config.true "push_enabled"; then push_enabled="true"; else push_enabled="false"; fi
    bashio::log.info "push_enabled: ${push_enabled}"
    $crudini --set /usr/local/bin/scgi_server/config.ini PUSH enabled "$push_enabled"

    # verbose level
    if bashio::config.has_value "verbose_level"; then verbose_level=$(bashio::config 'verbose_level'); else verbose_level="ERROR"; fi
    bashio::log.info "configured verbose_level: ${verbose_level}"
    $crudini --set /usr/local/bin/scgi_server/config.ini DEBUGLOG enabled true
    $crudini --set /usr/local/bin/scgi_server/config.ini DEBUGLOG verbose_level "$verbose_level"
    # log goes to stdout already, the log file is not needed
    $crudini --set /usr/local/bin/scgi_server/config.ini DEBUGLOG log_to_file false
    # older versions of this app wrote verbose_level into the wrong section
    $crudini --del /usr/local/bin/scgi_server/config.ini CACHE verbose_level


    # copy config file to app config folder
    cp /usr/local/bin/scgi_server/config.ini "$(bashio::config 'configuration_file')"
    bashio::exit.ok
fi
