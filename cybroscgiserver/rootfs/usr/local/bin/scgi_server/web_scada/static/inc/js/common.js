function attach_common_jq_events()
{
    $("input")
        .focus(function() {
            $(this).addClass("input_focused");
        })
        .blur(function() {
            $(this).removeClass("input_focused");
        });

    $("textarea")
        .focus(function() {
            $(this).addClass("textarea_focused");
        })
        .blur(function() {
            $(this).removeClass("textarea_focused");
        });

    $(".button").hover(
        function() {
            $(this).addClass("button_hover");
        },
        function() {
            $(this).removeClass("button_hover");
        });

    $(".hover_row")
        .mouseenter(function() {
            $(this).addClass("hover_active");
        })
        .mouseleave(function() {
            $(this).removeClass("hover_active");
        });
}
