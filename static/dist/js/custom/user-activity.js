let timer, currSeconds = 0;

function resetTimer() {

    /* Hide the timer text */


    /* Clear the previous interval */
    clearInterval(timer);

    /* Reset the seconds of the timer */
    currSeconds = 0;

    /* Set a new interval */
    timer = 
        setInterval(startIdleTimer, 1000);
}

// Define the events that
// would reset the timer
window.onload = resetTimer;
window.onmousemove = resetTimer;
window.onmousedown = resetTimer;
window.ontouchstart = resetTimer;
window.onclick = resetTimer;
window.onkeypress = resetTimer;

function startIdleTimer() {
        
    /* Increment the
        timer seconds */
    currSeconds++;

    /* Set the timer text
        to the new value */

    if(currSeconds == 600){
        // document.location.href = "logout/";
        window.location = "/logout/";
    }
}