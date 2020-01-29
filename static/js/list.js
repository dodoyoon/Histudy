function send(){
  $.ajax({
    type: "get",
    url: "",
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

