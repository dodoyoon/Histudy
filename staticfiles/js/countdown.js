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
            }
        }, 1000);
    }
}

function countdown() {
    if (is_timer_set == false){
        is_timer_set = true ;
        var tenMinutes = 60 * 10,
            display = document.querySelector('#time');
        startTimer(tenMinutes, display);
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
