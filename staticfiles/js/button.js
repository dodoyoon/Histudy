$(function(){
    $("#actasbutton").bind("click",function(){
        $("#dataform").submit();  // consider idOfYourForm `id` of your form which you are going to submit
    });
});

document.getElementById("actasbutton").onclick = function(){
    document.getElementById("dataform").submit();
};