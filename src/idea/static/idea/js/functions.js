$(document).ready(function() {

    // Hide the comment label when the input box is focused
    $(".comment-form form textarea")
        .focus(function(){
            $(".comment-label").hide();
            $('.id_comment').addClass('active');
        })
        .blur(function(){
            if (!this.value) {
                $(".comment-label").show();
                $('.id_comment').removeClass('active');
            }
    });

    //Change the button voted text to "unlike" on hover
    $(".btn-voted").hover(
        function(){
            $(this).val('Unlike');
        },
        function(){
            $(this).val('Liked');
        });

    function show_reply_form(event) {
        var $this = $(this);
        var comment_id = $this.data('comment-id');
        $('#parent_id').attr("value", comment_id);
        $('.comment-form').insertAfter($this.closest('.comment'));
    };

    function cancel_reply_form(event) {
        $('#id_comment').val('');
        $('#id_parent').val('');
        $('.comment-form').appendTo($('#comment-wrap'));
    };

    $.fn.ready(function() {
        $('.comment_reply_link').click(show_reply_form);
        $('#cancel_reply').click(cancel_reply_form);
    });

});
