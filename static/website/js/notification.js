function getFcmToken(currentToken) {
    $.ajax({
      url : "{% url 'push_notification:get_device_token' %}",
      type : 'post',
      data : {token: currentToken, csrfmiddlewaretoken: "{{csrf_token}}"}
    })
    return messaging.getToken()
  }

  var firebaseConfig = {
  apiKey: "AIzaSyCi7VjSzm2cTam3cddLDuk1NUcb0sP4zCI",
  authDomain: "growatpace.firebaseapp.com",
      databaseURL: "https://growatpace-default-rtdb.asia-southeast1.firebasedatabase.app",
      projectId: "growatpace",
      storageBucket: "growatpace.appspot.com",
      messagingSenderId: "151352292161",
      appId: "1:151352292161:web:5cc2cfb11defedee05a7c0",
      measurementId: "G-6Q6GSB9E9J"
    };
    // Initialize Firebase
    firebase.initializeApp(firebaseConfig);
    firebase.analytics();
  
    const messaging = firebase.messaging();
    console.log(messaging.getToken())
    messaging.getToken({ vapidKey: 'BIj6fa3eSeOv5UmujQnHbQ9MYemTerS7LNtPUTQ0p41r1h4qAtO3yWPAZM8G4TFbB_pQsVjArn3Yh45zfwJCiyM' }).then((currentToken) => {
    if (currentToken) {
      getFcmToken(currentToken);
      console.log(currentToken)
    } else {
      console.log('No registration token available. Request permission to generate one.');
   
    }
  }).catch((err) => {
    console.log('An error occurred while retrieving token. ', err);
  });
  
  
    messaging
     .requestPermission()
     .then(function () {
       console.log("Notification permission granted.");
      })
     .catch(function (err) {
     console.log("Unable to get permission to notify.", err);
   });
  
  
    messaging.onMessage((payload) => {
    console.log('Message received. ', payload);
   
  });