$(document).ready(function(){
  $('#navbar-profile-link').click(function(e){
    e.preventDefault();
    console.log('yep!');
    if (!$(this).hasClass('navbar-link-active')){
      $(this).addClass('navbar-link-active');
      $('.navbar-submenu-profile').show();
    } else {
      $(this).removeClass('navbar-link-active');
      $('.navbar-submenu-profile').hide();
    }
  })
  $('.show_settings').mouseenter(function(){
    console.log('enter');
    $(this).children('.integration-settings').show();
  }).mouseleave(function(){
    console.log('leave');
    $(this).children('.integration-settings').hide();
  })
})
