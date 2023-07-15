var userID;
var token;
var tokenHelix;
var clientID;
var opaqueID;
var channelID;

// Function to send POST request with data
function sendDataToServer(data) {
fetch(`https://willpile.com/click/${channelID}`, {
    method: 'POST',
    headers: {
    'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
})
.then(response => {
    if (response.ok) {
    console.log('Data sent successfully');
    } else {
    console.error('Error sending data:', response.status);
    }
})
.catch(error => {
    console.error('Error sending data:', error);
});
}


Twitch.ext.onAuthorized(function(auth) {
    // Handle authorization and initialization here
    // You can access the Twitch Extension API using 'Twitch.ext' within this function

    // Store user-related information in variables
    userID = Twitch.ext.viewer.id;
    token = auth.token;
    tokenHelix = auth.helixToken;
    clientID = auth.clientId;
    opaqueID = auth.userId;
    channelID = auth.channelId;
    
    var data = {
        action: "auth",
        user_id: userID,
        token: token,
        tokenHelix: tokenHelix,
        clientID: clientID,
        opaqueID: opaqueID,
        channelID: channelID
    };

    sendDataToServer(data)

    console.log(userID, opaqueID, clientID, channelID);
});

function handleLeftClick(event) {
    var x = event.clientX; // Get the horizontal coordinate of the click
    var y = event.clientY; // Get the vertical coordinate of the click

    // Normalize the coordinates as a percentage of the screen size
    var normalizedX = x / window.innerWidth;
    var normalizedY = y / window.innerHeight;
    
    data = {
        action: 'leftClick',
        x: normalizedX,
        y: normalizedY,
        opaque_id: opaqueID,
        user_id: userID
    };

    sendDataToServer(data);

    console.log("Left mouse button clicked at (" + normalizedX + ", " + normalizedY + ")");
}

function handleRightClick(event) {
    var x = event.clientX; // Get the horizontal coordinate of the click
    var y = event.clientY; // Get the vertical coordinate of the click

    // Normalize the coordinates as a percentage of the screen size
    var normalizedX = x / window.innerWidth;
    var normalizedY = y / window.innerHeight;

    data = {
        action: 'rightClick',
        x: normalizedX,
        y: normalizedY,
        opaque_id: opaqueID,
        user_id: userID
    };

    sendDataToServer(data);

    console.log("Right mouse button clicked at (" + normalizedX + ", " + normalizedY + ")");
    // Call your custom function for right-click here

    // Prevent the context menu from popping up
    event.preventDefault();
}

document.addEventListener("mousedown", function(event) {
    if (event.button === 0) {
        handleLeftClick(event);
    } else if (event.button === 2) {
        handleRightClick(event);
    }
});

document.addEventListener("contextmenu", function(event) {
    event.preventDefault();
});