$(document).ready(function() {

    $("#blastme").click(function(evt) {
        console.log('requesting')
        $("#blastme").prop('disabled', true);
        n = $("#count").val()
        if (n>100000) {
            $("#results").html("Now let's not get too crazy... my server has other stuff to do. How about keeping it under 100k?");
        } else {
            i = 0
            ws.send(n)
        }
    });
    $("#blastme").prop('disabled', true);
    $("#results").html('Connecting');
    
    ws = new WebSocket("ws://gokologs.drunkensailor.org/wshblast");
    
    ws.onopen = function(evt) {
        console.log('connected')
        $("#results").html('Connected');
        $("#blastme").prop('disabled', false);
    };
    
    ws.onmessage = function(msg) {
        if (i % 1000 === 0) {
            $("#results").html('Received ' + i + '/' + n + ' messages.');
        }
        if (i == n) {
            $("#results").html('Received ' + i + ' messages.<br>' + msg.data);
        };
        i = i + 1;
    }
});
