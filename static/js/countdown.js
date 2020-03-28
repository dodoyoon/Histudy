var is_timer_set = false ;

function startTimer(duration, display) {
    var timer = duration, minutes, seconds;

    if(is_timer_set == true){
        var timerId = setInterval(function () {
            minutes = parseInt(timer / 60, 10);
            seconds = parseInt(timer % 60, 10);

            minutes = minutes < 10 ? "0" + minutes : minutes;
            seconds = seconds < 10 ? "0" + seconds : seconds;

            display.textContent = minutes + ":" + seconds;

            if (--timer < 0) {
                timer = duration;
            }

            if(minutes == 0 && seconds == 0){
                is_timer_set = false ;
                clearTimeout(timerId);
                // hide_countdown();
            }
        }, 1000);
    }
}

function countdown(code_time) {
    code_time = 60 * 10 - code_time;

    if (is_timer_set == false){
        is_timer_set = true ;
        var display = document.querySelector('#time');

        minutes = parseInt(code_time / 60, 10);
        seconds = parseInt(code_time % 60, 10);

        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;


        if(code_time == 600){
            display.innerHTML = "10:00";
        }else{
            display.innerHTML = minutes + ":" + seconds;
        }

        startTimer(code_time, display);
    }
};

function hide_countdown(){
    var target = document.querySelector('#countdown_div');
    target.style.visibility = 'hidden' ;
}

function show_countdown(){
    var target = document.querySelector('#countdown_div');
    target.style.visibility = 'visible' ;
}
