// <!-- Display the countdown timer in an element -->
// <p id="countdown"></p>

  // Set the date we're counting down to
  var countDownDate = new Date(countDownDate_start).getTime();
  // Update the count down every 1 second
  var x = setInterval(function() {

  // Get todays date and time
  var now = new Date().getTime();

  if (countDownDate < now){
    countDownDate = new Date(countDownDate_end).getTime();
  }
  // Find the distance between now and the count down date
  var distance = countDownDate - now;
  
//   console.log(countDownDate_start, countDownDate, countDownDate_end , now, distance);

// Time calculations for days, hours, minutes and seconds
  // console.log(distance);
  var days = Math.floor(distance / (1000 * 60 * 60 * 24));
  var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
  var seconds = Math.floor((distance % (1000 * 60)) / 1000);

  if (seconds < 10) seconds = "0" + seconds;
  if (minutes < 10) minutes = "0" + minutes;
  if (hours < 10) hours = "0" + hours;
  // Display the result in the element with id="countdown"
  if (days > 0){
      document.getElementById("countdown").innerHTML = days + "d " + hours + ":" + minutes + ":" + seconds;
  }
  else{
      document.getElementById("countdown").innerHTML = hours + ":"+ minutes + ":" + seconds;
      }
  
  

  // If the count down is finished, write some text 
  if (distance <= 0) {
      clearInterval(x);
      document.getElementById("countdown").innerHTML = "";
  }
  }, 5);
    // </script>