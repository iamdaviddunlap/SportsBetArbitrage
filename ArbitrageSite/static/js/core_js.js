
response = [{"sport_title": "CFL", "sport_id": "americanfootball_cfl", "arb_games": []}, {"sport_title": "NCAAF", "sport_id": "americanfootball_ncaaf", "arb_games": [{"home": "Old Dominion Monarchs", "away": "Arkansas State Red Wolves", "expected_profit": 3.82, "worst_case_profit": 3.6, "home_bookmaker": {"name": "draftkings", "odds_eu": 2.8, "odds_us": 180, "bet": 37}, "away_bookmaker": {"name": "bovada", "odds_eu": 1.65, "odds_us": -154, "bet": 63}}, {"home": "Georgia Southern Eagles", "away": "Ball State Cardinals", "expected_profit": 1.88, "worst_case_profit": 1.84, "home_bookmaker": {"name": "barstool", "odds_eu": 1.34, "odds_us": -294, "bet": 76}, "away_bookmaker": {"name": "fanduel", "odds_eu": 4.25, "odds_us": 325, "bet": 24}}, {"home": "East Carolina Pirates", "away": "Navy Midshipmen", "expected_profit": 4.13, "worst_case_profit": 4.0, "home_bookmaker": {"name": "bovada", "odds_eu": 1.24, "odds_us": -417, "bet": 84}, "away_bookmaker": {"name": "barstool", "odds_eu": 6.5, "odds_us": 550, "bet": 16}}, {"home": "Troy Trojans", "away": "Marshall Thundering Herd", "expected_profit": 5.31, "worst_case_profit": 5.08, "home_bookmaker": {"name": "draftkings", "odds_eu": 1.48, "odds_us": -208, "bet": 71}, "away_bookmaker": {"name": "fanduel", "odds_eu": 3.65, "odds_us": 265, "bet": 29}}, {"home": "New Mexico State Aggies", "away": "Hawaii Rainbow Warriors", "expected_profit": 1.23, "worst_case_profit": 0.45, "home_bookmaker": {"name": "bovada", "odds_eu": 2.05, "odds_us": 105, "bet": 49}, "away_bookmaker": {"name": "draftkings", "odds_eu": 2.0, "odds_us": 100, "bet": 51}}]}, {"sport_title": "NFL", "sport_id": "americanfootball_nfl", "arb_games": []}, {"sport_title": "MLB", "sport_id": "baseball_mlb", "arb_games": [{"home": "Arizona Diamondbacks", "away": "San Francisco Giants", "expected_profit": 0.51, "worst_case_profit": 0.35, "home_bookmaker": {"name": "betrivers", "odds_eu": 1.83, "odds_us": -120, "bet": 55}, "away_bookmaker": {"name": "barstool", "odds_eu": 2.23, "odds_us": 123, "bet": 45}}]}, {"sport_title": "NBA", "sport_id": "basketball_nba", "arb_games": []}, {"sport_title": "CPLT20", "sport_id": "cricket_caribbean_premier_league", "arb_games": []}, {"sport_title": "ICC World Cup", "sport_id": "cricket_icc_world_cup", "arb_games": []}, {"sport_title": "International Twenty20", "sport_id": "cricket_international_t20", "arb_games": []}, {"sport_title": "NHL", "sport_id": "icehockey_nhl", "arb_games": []}, {"sport_title": "MMA", "sport_id": "mma_mixed_martial_arts", "arb_games": []}]

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