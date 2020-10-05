$(document).ready(function(){
  $('#navbar-profile-link').click(function(e){
    e.preventDefault();
    // console.log('yep!');
    if (!$(this).hasClass('navbar-link-active')){
      $(this).addClass('navbar-link-active');
      $('.navbar-submenu-profile').show();
    } else {
      $(this).removeClass('navbar-link-active');
      $('.navbar-submenu-profile').hide();
    }
  })
  $('.show_settings').mouseenter(function(){
    // console.log('enter');
    $(this).children('.integration-settings').show();
  }).mouseleave(function(){
    // console.log('leave');
    $(this).children('.integration-settings').hide();
  })
})

function getSelectedGoals(){
  var select = document.getElementById('goals');
  var selected_goals = [...select.selectedOptions]
                     .map(option => option.value);
  return selected_goals;
}

function setTotalUniqueVisitors(total_unique_visitors){
  document.getElementById('total_unique_visitors').innerHTML =
                                            'Выбрано <b>' +
                                            total_unique_visitors +
                                            "</b> уникальных посетителей"
                                            ;
}

function setTotalEmailVisitors(total_email_visitors){
  document.getElementById('total_email_visitors').innerHTML=
                                            'Из них <b>' +
                                            total_email_visitors +
                                            '</b> хотя бы раз перешли из email'

}