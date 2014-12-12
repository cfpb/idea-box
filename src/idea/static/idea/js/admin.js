(function($) {

// In Django Admin page for Idea Banner, if Private is set, display option to
// enable or disable votes.  If Private is unchecked, for the voting to
// be set to true and hide the checkbox
function set_votes_visibility() {
    if ($('.field-box.field-is_private > input').is(':checked')) {
        $('.field-box.field-is_votes').show(); 
        $('.field-box.field-room_link_clickable').show(); 
    } else {
        $('.field-box.field-is_votes').hide();
        $('.field-box.field-room_link_clickable').hide();
        $('.field-box.field-is_votes > input').attr('checked', 'checked');
    }
};
$(document).ready(function() {
    $('.field-box.field-is_private > input').click(set_votes_visibility);

    set_votes_visibility();
});

})(django.jQuery);
