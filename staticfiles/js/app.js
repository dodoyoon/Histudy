function send(){
  $.ajax({
    type: "get",
    url: "all",
    success:function(data)
    {
      $("html").html(data);
      console.log(data);
      setTimeout(function(){
        send();
      }, 10000);
    }
  });
}

//Call our function
send();

$(document).ready(function(){
    $(".close").click(function(){
  $("#myAlert").alert("close");
});
  // Activate Carousel
  $("#myCarousel").carousel();
    
  // Enable Carousel Indicators
  $(".item1").click(function(){
    $("#myCarousel").carousel(0);
  });
  $(".item2").click(function(){
    $("#myCarousel").carousel(1);
  });
  $(".item3").click(function(){
    $("#myCarousel").carousel(2);
  });
    
  // Enable Carousel Controls
  $(".carousel-control-prev").click(function(){
    $("#myCarousel").carousel("prev");
  });
  $(".carousel-control-next").click(function(){
    $("#myCarousel").carousel("next");
  });
});