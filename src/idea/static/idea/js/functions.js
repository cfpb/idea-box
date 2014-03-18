$(document).ready(function() {
	$('.idea-entry').hover(function(){
		$(this).addClass('hover'); 
	}, function() {
		$(this).removeClass('hover');
	});

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
});
