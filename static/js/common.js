
$(function(){
	
	$(".btn_top").click(function(){
        $('body,html').stop().animate({scrollTop: 0 }, 600);
    });

	$(".menu_bar").click(function(){
		if($(".sub_menu_m").hasClass("on")) {
			$(".sub_menu_m").removeClass("on");
			$(".menu_bar").removeClass("on");
		}else {

			$('.sub_menu_m').addClass("on");
			$(".menu_bar").addClass("on");
		}        
    });

	$(".top_menu .m a.d").mouseover(function(){
		if(document.body.offsetWidth>640){ 
			$(".top_menu").addClass("on");
		}
		
    });

	$(".top_area").mouseleave(function(){
		$(".top_menu").removeClass("on");
    });

	$(".sub_txt2 span").click(function(){
		if($(".sub_box2").hasClass("on")) {
			$(".sub_box2").removeClass("on");
		}else {

			$(".sub_box2").addClass("on");
		}        
    });

	
	$(".sub_box4 li.liver").click(function(){
		if($(".sub_result_pop4").hasClass("on")) {
			$(".sub_result_pop4").removeClass("on");
		}else {

			$(".sub_result_pop4").addClass("on");
		}        
    });

		$(".sub_box4 li.Similarity").click(function(){
		if($(".sub_result_pop").hasClass("on")) {
			$(".sub_result_pop").removeClass("on");
		}else {

			$(".sub_result_pop").addClass("on");
		}        
    });

	$(".sub_box4 li.hepa_1").click(function(){
		if($(".sub_result_pop2").hasClass("on")) {
			$(".sub_result_pop2").removeClass("on");
		}else {

			$(".sub_result_pop2").addClass("on");
		}        
    });


	$(".sub_box4 li.hepa_2").click(function(){
		if($(".sub_result_pop3").hasClass("on")) {
			$(".sub_result_pop3").removeClass("on");
		}else {

			$(".sub_result_pop3").addClass("on");
		}        
    });


	$(".top_menu .m a:nth-child(2)").click(function(){
		$(".top_menu").addClass("on");
		$(".sub_menu_p li").removeClass("on");
		$(".sub_menu_p li.sub1").addClass("on");
    });

	$(".top_menu .m a:nth-child(3)").click(function(){
		$(".top_menu").addClass("on");
		$(".sub_menu_p li").removeClass("on");
		$(".sub_menu_p li.sub2").addClass("on");
    });

	$(".top_menu .m a:nth-child(4)").click(function(){
		$(".top_menu").addClass("on");
		$(".sub_menu_p li").removeClass("on");
		$(".sub_menu_p li.sub3").addClass("on");
    });

	

});


$(document).ready(function(){ 
	var fileTarget = $('.filebox .upload-hidden'); 

		fileTarget.on('change', function(){ // 媛믪씠 蹂�寃쎈릺硫� 
		if(window.FileReader){ // modern browser 
			var filename = $(this)[0].files[0].name; 
		} 
		else { // old IE 
			var filename = $(this).val().split('/').pop().split('\\').pop(); // �뚯씪紐낅쭔 異붿텧 
		} 
		
		// 異붿텧�� �뚯씪紐� �쎌엯 
		$(this).siblings('.upload-name').val(filename); 
	}); 
}); 

$(window).load(function(e) {
	
});

$(window).resize(function(e) {
	
});

