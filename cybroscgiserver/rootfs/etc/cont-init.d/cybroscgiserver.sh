#!/command/with-contenv bashio
# ==============================================================================
# Home Assistant Community App: CybroScgiServer
# Pre-run checks for CybroScgiServer
# ==============================================================================
declare autodetect_address
declare host_interface
declare host_address
declare broadcast
declare push_enabled
declare verbose_level
declare configuration_file
declare controllers
declare migrated
declare controller_sections

crudini="crudini"

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

# ip address of the network interface with the default route (only logged for now)
# the app uses the host network, so the host interfaces are visible here
host_interface=$(ip -4 route show default 2>/dev/null | awk '{ for (i = 1; i < NF; i++) if ($i == "dev") { print $(i + 1); exit } }' || true)
host_address=""
if [[ -n "${host_interface}" ]]; then
    host_address=$(ip -o -4 addr show dev "${host_interface}" 2>/dev/null | awk '{ print $4; exit }' || true)
fi
if [[ "${host_address}" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)/([0-9]+)$ ]]; then
    ip_int=$(( (BASH_REMATCH[1] << 24) | (BASH_REMATCH[2] << 16) | (BASH_REMATCH[3] << 8) | BASH_REMATCH[4] ))
    mask=$(( (0xFFFFFFFF << (32 - BASH_REMATCH[5])) & 0xFFFFFFFF ))
    bc_int=$(( ip_int | (~mask & 0xFFFFFFFF) ))
    broadcast="$(( bc_int >> 24 & 255 )).$(( bc_int >> 16 & 255 )).$(( bc_int >> 8 & 255 )).$(( bc_int & 255 ))"
    bashio::log.info "ip address (${host_interface}): ${host_address}, broadcast address: ${broadcast}"
else
    bashio::log.info "could not get the ip address of interface ${host_interface:-(none)}"
fi

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

# manual controllers
controllers=$(jq -c '.controllers // []' /data/options.json)

# migrate controllers from the config file used by older versions of this app
if [[ "$(jq 'length' <<< "${controllers}")" -eq 0 ]]; then
    if bashio::config.has_value "configuration_file"; then
        configuration_file=$(bashio::config 'configuration_file')
    else
        configuration_file="/config/cybroscgiserver_config.ini"
    fi
    # very old versions of this app stored the file in the homeassistant config folder
    for legacy_file in "${configuration_file}" "${configuration_file/"/config"/"/homeassistant"}"; do
        if ! bashio::fs.file_exists "${legacy_file}"; then
            continue
        fi
        bashio::log.info "Found old config file: ${legacy_file}"
        migrated="[]"
        for section in $($crudini --get "${legacy_file}"); do
            if [[ ! "${section}" =~ ^c[0-9]+$ ]]; then
                continue
            fi
            ip=$($crudini --get "${legacy_file}" "${section}" ip 2>/dev/null || true)
            port=$($crudini --get "${legacy_file}" "${section}" port 2>/dev/null || true)
            password=$($crudini --get "${legacy_file}" "${section}" password 2>/dev/null || true)
            [[ "${port}" =~ ^[0-9]+$ ]] || port=""
            [[ "${password}" =~ ^[0-9]+$ ]] || password=""
            migrated=$(jq -c --arg nad "${section#c}" --arg ip "${ip}" --arg port "${port}" --arg password "${password}" \
                '. + [{nad: ($nad | tonumber), ip: $ip}
                    + (if $port != "" then {port: ($port | tonumber)} else {} end)
                    + (if $password != "" then {password: ($password | tonumber)} else {} end)]' \
                <<< "${migrated}")
        done
        if [[ "$(jq 'length' <<< "${migrated}")" -gt 0 ]]; then
            if ! bashio::addon.option 'controllers' "^${migrated}"; then
                bashio::log.error "Could not save the controllers into the app options, trying again on next start"
                break
            fi
            bashio::log.info "Imported $(jq 'length' <<< "${migrated}") controller(s) into the app options"
            # options.json is only rewritten on the next start, so use them directly
            controllers="${migrated}"
        fi
        bashio::log.info "The config file is not used anymore, renaming it to ${legacy_file}.migrated"
        mv "${legacy_file}" "${legacy_file}.migrated"
        break
    done
fi

# remove controllers written by a previous start, so removed entries don't stay
for section in $($crudini --get /usr/local/bin/scgi_server/config.ini); do
    if [[ "${section}" =~ ^c[0-9]+$ ]]; then
        $crudini --del /usr/local/bin/scgi_server/config.ini "${section}"
    fi
done
# each nad can only be configured once, keep the first entry
for nad in $(jq -r 'group_by(.nad)[] | select(length > 1) | .[0].nad' <<< "${controllers}"); do
    bashio::log.warning "controller c${nad} is configured more than once, only the first entry is used"
done
controllers=$(jq -c 'reduce .[] as $c ([]; if any(.[]; .nad == $c.nad) then . else . + [$c] end)' <<< "${controllers}")
controller_sections=""
while read -r controller; do
    nad=$(jq -r '.nad' <<< "${controller}")
    ip=$(jq -r '.ip' <<< "${controller}")
    port=$(jq -r '.port // 8442' <<< "${controller}")
    password=$(jq -r '.password // ""' <<< "${controller}")
    bashio::log.info "manual controller: c${nad} (${ip}:${port})"
    controller_sections+="[c${nad}]"$'\n'"ip = ${ip}"$'\n'"port = ${port}"$'\n'"password = ${password}"$'\n\n'
done < <(jq -c '.[]' <<< "${controllers}")
# controllers belong right after the ETH section, so insert them before [PUSH]
if [[ -n "${controller_sections}" ]]; then
    awk -v sections="${controller_sections}" '/^\[PUSH\]/ { printf "%s", sections } { print }' \
        /usr/local/bin/scgi_server/config.ini > /tmp/config.ini
    mv /tmp/config.ini /usr/local/bin/scgi_server/config.ini
fi

bashio::exit.ok

