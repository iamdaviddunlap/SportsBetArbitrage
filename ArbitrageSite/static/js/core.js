
let update_freq = parseInt($('#update-freq').val());
let pulling = false;  // The program starts will pulling off
let lockout = false;  // This is set to true when calling the api to prevent it getting called again before returning
let intervalId = null;  // There is no interval running at program start

$(document).ready(function(){

    $("#toggle-pulls-bttn").click(function(){
        if(pulling) {
            // This means we are turning OFF the pulling
            pulling = false;
            $("#toggle-pulls-bttn").removeClass('red');
            $("#toggle-pulls-bttn").addClass('green');
            $("#toggle-pulls-bttn").text('Start');
            handleInterval();
        } else {
            // This means we are turning ON the pulling
            pulling = true;
            $("#toggle-pulls-bttn").removeClass('green');
            $("#toggle-pulls-bttn").addClass('red');
            $("#toggle-pulls-bttn").text('Stop');
            handleInterval();
        }
    });
});


function handleInterval() {
    /* This function is called when there is a change to the interval (i.e. the toggle button was clicked) */
    if(pulling) {
        // This means we are turning ON the pulling
        console.log('turning on pulling');
        let next_date = new Date();
        next_date = next_date.setSeconds(next_date.getSeconds() + update_freq);

        $("#next-refresh").text('Next refresh: '+new Date(next_date).toLocaleTimeString());
        intervalId = window.setInterval(function(){
            let cur_date = new Date();
            let next_date = new Date();
            next_date = next_date.setSeconds(next_date.getSeconds() + update_freq);
            $("#last-refresh").text('Last refresh: '+new Date(cur_date).toLocaleTimeString());
            $("#next-refresh").text('Next refresh: '+new Date(next_date).toLocaleTimeString());

            call_api();
        }, update_freq*1000);
    } else {
        // This means we are turning OFF the pulling
        console.log('turning off pulling');
        clearInterval(intervalId);
        $("#last-refresh").text('Last refresh:');
        $("#next-refresh").text('Next refresh:');
    }
}


function call_api() {
    if(!lockout) {
        lockout = true;
        $.ajax({
            url: "/query-arbitrage",
            type: 'GET',
            dataType: 'json',
            success: function(res) {
                console.log(res);
                process_response(res);
            }
        });
        lockout = false;
    } else {
        console.log('Ignoring call to call_api() because of lockout');
    }
}


function process_response(response) {
    let arb_obj = response.arb_obj;
    let remaining_requests = response.remaining_requests;
    $("#requests-left").text('Requests left with API Key: '+remaining_requests);

    $("#card-holder").empty();

    arb_obj.forEach(sport_obj => {

        $('<div class="col s12" id="'+sport_obj.sport_id+'_holder"></div>').appendTo('#card-holder');
        $('<h4>'+sport_obj.sport_title+'</h4>').appendTo('#'+sport_obj.sport_id+'_holder');

        sport_obj.arb_games.forEach(game_obj => {
            $('<div class="card horizontal">' +
                '  <div class="card-content">' +
                '    <h5>'+game_obj.home+' vs '+game_obj.away+'</h5>' +
                '    <h6>Expected profit: $'+game_obj.expected_profit+' <br/> Worst case profit: $'+game_obj.worst_case_profit+'</h6>' +
                '    <p><b>'+game_obj.home_bookmaker.name+'</b> <br/>' +
                '    Bet $'+game_obj.home_bookmaker.bet+' on '+game_obj.home+' ('+game_obj.home_bookmaker.odds_eu+' / '+game_obj.home_bookmaker.odds_us+')' +
                '    </p><br/>' +
                '    <p><b>'+game_obj.away_bookmaker.name+'</b> <br/>' +
                '    Bet $'+game_obj.away_bookmaker.bet+' on '+game_obj.away+' ('+game_obj.away_bookmaker.odds_eu+' / '+game_obj.away_bookmaker.odds_us+')' +
                '    </p>' +
                '  </div>' +
                '</div>').appendTo('#'+sport_obj.sport_id+'_holder');
        });

        $('<hr style="height:3px; color:black; background-color:black;"/>').appendTo('#'+sport_obj.sport_id+'_holder');
    });
}