
response = [{"sport_title": "CFL", "sport_id": "americanfootball_cfl", "arb_games": [{"home": "Ottawa Redblacks", "away": "Toronto Argonauts", "expected_profit": 31.07, "worst_case_profit": 30.0, "home_bookmaker": {"name": "Bovada", "odds_eu": 10.0, "odds_us": 900, "bet": 13}, "away_bookmaker": {"name": "FanDuel", "odds_eu": 1.51, "odds_us": -196, "bet": 87}}]}, {"sport_title": "NCAAF", "sport_id": "americanfootball_ncaaf", "arb_games": [{"home": "Northwestern Wildcats", "away": "Miami (OH) RedHawks", "expected_profit": 8.09, "worst_case_profit": 7.36, "home_bookmaker": {"name": "FanDuel", "odds_eu": 1.76, "odds_us": -132, "bet": 61}, "away_bookmaker": {"name": "Bovada", "odds_eu": 2.8, "odds_us": 180, "bet": 39}}, {"home": "Oklahoma Sooners", "away": "Kansas State Wildcats", "expected_profit": 4.63, "worst_case_profit": 3.84, "home_bookmaker": {"name": "Barstool Sportsbook", "odds_eu": 1.76, "odds_us": -132, "bet": 59}, "away_bookmaker": {"name": "FanDuel", "odds_eu": 2.58, "odds_us": 158, "bet": 41}}]}, {"sport_title": "NFL", "sport_id": "americanfootball_nfl", "arb_games": []}, {"sport_title": "MLB", "sport_id": "baseball_mlb", "arb_games": []}, {"sport_title": "NBA", "sport_id": "basketball_nba", "arb_games": []}, {"sport_title": "CPLT20", "sport_id": "cricket_caribbean_premier_league", "arb_games": []}, {"sport_title": "ICC World Cup", "sport_id": "cricket_icc_world_cup", "arb_games": []}, {"sport_title": "International Twenty20", "sport_id": "cricket_international_t20", "arb_games": []}, {"sport_title": "NHL", "sport_id": "icehockey_nhl", "arb_games": []}, {"sport_title": "MMA", "sport_id": "mma_mixed_martial_arts", "arb_games": []}]

$(document).ready(function(){
    process_response(response);
});


function process_response(response) {
    response.forEach(sport_obj => {

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