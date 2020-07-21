import mysql.connector
from mysql.connector import errorcode
import pandas as pd
import numpy as np
import matplotlib
from bokeh.plotting import figure, ColumnDataSource, show
from bokeh.embed import components
from bokeh.resources import CDN
from bokeh.palettes import RdYlBu7 as palette
from bokeh.models import HoverTool, LinearColorMapper, LabelSet, ColumnDataSource, DataRange1d, Select, DataCube, DateFormatter, TableColumn, GroupingInfo, SumAggregator, Div
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.client import push_session, pull_session
from math import pi

"""
Global Variables
"""
# Information for connecting to database
config_info = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Kirby123Dustin!'
}
db_name = 'nba_database'

# Comparison options
comp_dict = {
            'Field Goal Percentage':'fg_perc',
            'Shooting Foul Rate':'shooting_foul_rate',
            'And-One Rate':'and_one_rate',
            'Shot Assisted Rate':'ast_rate',
            'Shot Blocked Rate':'blk_rate'}

# Queries
player_query = "SELECT player_full, player_id, player_last, player_first FROM nba_players WHERE is_active=%s"
shots_query = ("""
            SELECT
            	nba_shots.shot_type,
            	nba_shots.shot_zone_basic,
            	nba_shots.shot_zone_area,
            	nba_shots.shot_distance,
            	nba_shots.loc_x,
            	nba_shots.loc_y,
            	nba_shots.shot_attempted,
            	nba_shots.shot_made,
            	nba_shots.shot_foul,
            	nba_shots.shot_assist,
            	nba_shots.shot_block
            FROM nba_database.nba_shots
            LEFT JOIN nba_database.nba_games
            	ON nba_shots.game_id = nba_games.game_id
            LEFT JOIN nba_database.nba_players
            	ON nba_shots.player_id = nba_players.player_id
            LEFT JOIN nba_database.nba_teams
            	ON nba_shots.team_id = nba_teams.team_id
            WHERE
            	nba_games.season_type='Regular' AND
                nba_games.season = '2018' AND
                nba_shots.player_id='2037';
                """)
seasons_query = ("""
            SELECT DISTINCT nba_games.season
            FROM nba_database.nba_shots
            LEFT JOIN nba_database.nba_games
            	ON nba_shots.game_id = nba_games.game_id
            LEFT JOIN nba_database.nba_players
            	ON nba_shots.player_id = nba_players.player_id
            WHERE
              nba_games.season_type='Regular' AND
              nba_shots.player_id= %s;
            """)
data_cube_summary = ("""
                SELECT
                	' League ' as grouped,
                    CONCAT(nba_shots.shot_zone_basic, ' ', nba_shots.shot_zone_area) as shot_zone,
                	SUM(nba_shots.shot_made) as fgm,
                	SUM(CASE WHEN((nba_shots.shot_made=1 AND nba_shots.shot_foul=1) OR nba_shots.shot_foul=0) THEN 1 ELSE 0 END) as fga,
                	SUM(nba_shots.shot_foul) as fouls,
                	SUM(CASE WHEN(nba_shots.shot_made=1 AND nba_shots.shot_foul=1) THEN 1 ELSE 0 END) as and_1,
                	SUM(nba_shots.shot_assist) as ast,
                	SUM(nba_shots.shot_block) as blk,
                	SUM(nba_shots.shot_attempted) as t_fga,
                	SUM(nba_shots.shot_made)/SUM(CASE WHEN((nba_shots.shot_made=1 AND nba_shots.shot_foul=1) OR nba_shots.shot_foul=0) THEN 1 ELSE 0 END) as fg_perc,
                	SUM(nba_shots.shot_foul)/SUM(nba_shots.shot_attempted) as shooting_foul_rate,
                	SUM(CASE WHEN(nba_shots.shot_made=1 AND nba_shots.shot_foul=1) THEN 1 ELSE 0 END)/SUM(nba_shots.shot_foul) as and_one_rate,
                	SUM(nba_shots.shot_assist)/SUM(nba_shots.shot_made) as ast_rate,
                	SUM(nba_shots.shot_block)/SUM(nba_shots.shot_attempted) as blk_rate
                FROM nba_database.nba_shots
                LEFT JOIN nba_database.nba_games
                	ON nba_shots.game_id = nba_games.game_id
                LEFT JOIN nba_database.nba_players
                	ON nba_shots.player_id = nba_players.player_id
                WHERE
                	nba_games.season_type='Regular' AND
                	nba_games.season = %s
                GROUP BY LEFT(shot_zone, 21)
                UNION ALL
                SELECT
                	' Player ' as grouped,
                    CONCAT(nba_shots.shot_zone_basic, ' ', nba_shots.shot_zone_area) as shot_zone,
                	SUM(nba_shots.shot_made) as fgm,
                	SUM(CASE WHEN((nba_shots.shot_made=1 AND nba_shots.shot_foul=1) OR nba_shots.shot_foul=0) THEN 1 ELSE 0 END) as fga,
                	SUM(nba_shots.shot_foul) as fouls,
                	SUM(CASE WHEN(nba_shots.shot_made=1 AND nba_shots.shot_foul=1) THEN 1 ELSE 0 END) as and_1,
                	SUM(nba_shots.shot_assist) as ast,
                	SUM(nba_shots.shot_block) as blk,
                	SUM(nba_shots.shot_attempted) as t_fga,
                	SUM(nba_shots.shot_made)/SUM(CASE WHEN((nba_shots.shot_made=1 AND nba_shots.shot_foul=1) OR nba_shots.shot_foul=0) THEN 1 ELSE 0 END) as fg_perc,
                	SUM(nba_shots.shot_foul)/SUM(nba_shots.shot_attempted) as shooting_foul_rate,
                	SUM(CASE WHEN(nba_shots.shot_made=1 AND nba_shots.shot_foul=1) THEN 1 ELSE 0 END)/SUM(nba_shots.shot_foul) as and_one_rate,
                	SUM(nba_shots.shot_assist)/SUM(nba_shots.shot_made) as ast_rate,
                	SUM(nba_shots.shot_block)/SUM(nba_shots.shot_attempted) as blk_rate
                FROM nba_database.nba_shots
                LEFT JOIN nba_database.nba_games
                	ON nba_shots.game_id = nba_games.game_id
                LEFT JOIN nba_database.nba_players
                	ON nba_shots.player_id = nba_players.player_id
                WHERE
                	nba_games.season_type='Regular' AND
                	nba_games.season = %s AND
                    nba_shots.player_id = %s
                GROUP BY LEFT(shot_zone, 21);
            """)

def get_players(cursor, cxn, query, is_active=1):
    players={}
    cursor.execute(query, (is_active,))
    keys=cursor.description
    results=cursor.fetchall()
    col_names = [col[0] for col in keys]
    for row in results:
        i = 0
        name=row[0]
        players[name]={}
        for c in col_names:
            players[name][c]=row[i]
            i = i+1
    return players

def get_seasons(cursor, cxn, query, player):
    s_list = []
    cursor.execute(query, (player,))
    results=cursor.fetchall()
    for r in results:
        s_list.append(r[0])

    return s_list

def get_data(cursor, cxn, query, season, player):
    cursor.execute(query, (season, season, player))
    records = cursor.fetchall()
    field_names = [i[0] for i in cursor.description]
    df = pd.DataFrame(data=records, columns=field_names)
    return df

def bokeh_draw_court(figure, line_color='gray', line_width=1):
    """Returns a figure with the basketball court lines drawn onto it
    This function draws a court based on the x and y-axis values that the NBA
    stats API provides for the shot chart data.  For example the center of the
    hoop is located at the (0,0) coordinate.  Twenty-two feet from the left of
    the center of the hoop in is represented by the (-220,0) coordinates.
    So one foot equals +/-10 units on the x and y-axis.
    Parameters
    ----------
    figure : Bokeh figure object
        The Axes object to plot the court onto.
    line_color : str, optional
        The color of the court lines. Can be a a Hex value.
    line_width : float, optional
        The linewidth the of the court lines in pixels.
    Returns
    -------
    figure : Figure
        The Figure object with the court on it.
    """

    # hoop
    figure.circle(x=0, y=0, radius=7.5, fill_alpha=0,
                  line_color=line_color, line_width=line_width)

    # backboard
    figure.line(x=range(-30, 31), y=-12.5, line_color=line_color)

    # The paint
    # outerbox
    figure.rect(x=0, y=47.5, width=160, height=190, fill_alpha=0,
                line_color=line_color, line_width=line_width)
    # innerbox
    # left inner box line
    figure.line(x=-60, y=np.arange(-47.5, 143.5), line_color=line_color,
                line_width=line_width)
    # right inner box line
    figure.line(x=60, y=np.arange(-47.5, 143.5), line_color=line_color,
                line_width=line_width)

    # Restricted Zone
    #igure.arc(x=0, y=0, radius=40, start_angle=pi, end_angle=0,
               #line_color=line_color, line_width=line_width)

    # top free throw arc
    figure.arc(x=0, y=142.5, radius=60, start_angle=pi, end_angle=0,
               line_color=line_color)

    # bottome free throw arc
    figure.arc(x=0, y=142.5, radius=60, start_angle=0, end_angle=pi,
               line_color=line_color, line_dash="dashed")

    # Three point line
    # corner three point lines
    figure.line(x=-220, y=np.arange(-47.5, 87.5), line_color=line_color,
                line_width=line_width)
    figure.line(x=220, y=np.arange(-47.5, 87.5), line_color=line_color,
                line_width=line_width)
    # # three point arc
    #figure.arc(x=0, y=0, radius=237.5, start_angle=3.528, end_angle=-0.3863,
               #line_color=line_color, line_width=line_width)

    # add center court
    # outer center arc
    figure.arc(x=0, y=422.5, radius=60, start_angle=0, end_angle=pi,
               line_color=line_color, line_width=line_width)
    # inner center arct
    figure.arc(x=0, y=422.5, radius=20, start_angle=0, end_angle=pi,
               line_color=line_color, line_width=line_width)

    # outer lines, consistting of half court lines and out of bounds lines
    figure.rect(x=0, y=187.5, width=500, height=470, fill_alpha=0,
                line_color=line_color, line_width=line_width)

    return figure

def bokeh_shot_chart(source, title, x="X", y="Y", name="AREA", player="PLAYER", league="LEAGUE",
                    diff="PERC_DIFF", made="MADE", total="TOTAL", fgperc="PERC_FG",
                    fouls="PERC_SF", and_one="PERC_A1",
                    blk="PERC_BLK", ast="PERC_AST",fill_color="#1f77b4",
                     scatter_size=10, fill_alpha=0.4, line_alpha=0.4,
                     court_line_color='gray', court_line_width=1, **kwargs):

    #from bokeh.palettes import RdYlBu5
    #from bokeh.models import HoverTool, ColumnDataSource, LinearColorMapper
    """
    Returns a figure with both FGA and basketball court lines drawn onto it.
    This function expects data to be a ColumnDataSource with the x and y values
    named "LOC_X" and "LOC_Y".  Otherwise specify x and y.
    Parameters
    ----------
    data : DataFrame
        The DataFrame that contains the shot chart data.
    x, y : str, optional
        The x and y coordinates of the shots taken.
    fill_color : str, optional
        The fill color of the shots. Can be a a Hex value.
    scatter_size : int, optional
        The size of the dots for the scatter plot.
    fill_alpha : float, optional
        Alpha value for the shots. Must be a floating point value between 0
        (transparent) to 1 (opaque).
    line_alpha : float, optiona
        Alpha value for the outer lines of the plotted shots. Must be a
        floating point value between 0 (transparent) to 1 (opaque).
    court_line_color : str, optional
        The color of the court lines. Can be a a Hex value.
    court_line_width : float, optional
        The linewidth the of the court lines in pixels.
    hover_tool : boolean, optional
        If ``True``, creates hover tooltip for the plot.
    tooltips : List of tuples, optional
        Provides the information for the the hover tooltip.
    Returns
    -------
    fig : Figure
        The Figure object with the shot chart plotted on it.
    """
    cmap = LinearColorMapper(palette=palette, low=-10, high=10)

    TOOLS = "reset,hover,save"

    fig = figure(width=700, height=658, tools=TOOLS, x_range=[-250, 250],
                 y_range=[422.5, -47.5], min_border=0, x_axis_type=None,
                 y_axis_type=None, outline_line_color="black", **kwargs)

    fig.title.text = title

    bokeh_draw_court(fig, line_color=court_line_color,
                     line_width=court_line_width)

    fig.patches(x, y, source=source, line_color="black",
                fill_color={'field': diff, 'transform': cmap},
                alpha=fill_alpha, line_width=3)

    labels=[
        ("Area", "@AREA"),
        ("FGM", "@MADE"),
        ("FGA", "@TOTAL"),
        ("FG%", "@PERC_FG%"),
        ("SF%", "@PERC_SF%"),
        ("A-1%", "@PERC_A1%"),
        ("Assisted", "@PERC_AST%"),
        ("Blocked", "@PERC_BLK%"),
        ("Diff", "@PERC_DIFF%")
    ]

    hover = fig.select_one(HoverTool)
    hover.point_policy = "follow_mouse"
    hover.tooltips = labels

    return fig

def summary(df, comparison='fg_perc'):
    data_list = []

    # Restricted Area
    name = 'Restricted Area'
    theta = np.linspace(0, np.pi, 100)
    x1 = 40*np.cos(theta)
    x2 = np.array([-40, 40, 40])
    y1 = 40*np.sin(theta)
    y2 = np.array([-47.5, -47.5, 0])
    x = np.concatenate((x1, x2))
    y = np.concatenate((y1, y2))

    comp_player = df[(df['shot_zone']=='Restricted Area Center(C)') & (df['grouped']==' Player ')][comparison]*100
    comp_league = df[(df['shot_zone']=='Restricted Area Center(C)') & (df['grouped']==' League ')][comparison]*100
    if len(comp_player)!=0:
        diff = ((float(comp_player)-float(comp_league))/float(comp_league))*100
    else:
        diff = 0

    fgm = df[(df['shot_zone']=='Restricted Area Center(C)') & (df['grouped']==' Player ')]['fgm']
    fga = df[(df['shot_zone']=='Restricted Area Center(C)') & (df['grouped']==' Player ')]['fga']
    foul = df[(df['shot_zone']=='Restricted Area Center(C)') & (df['grouped']==' Player ')]['fouls']
    a1 = df[(df['shot_zone']=='Restricted Area Center(C)') & (df['grouped']==' Player ')]['and_1']
    ast = df[(df['shot_zone']=='Restricted Area Center(C)') & (df['grouped']==' Player ')]['ast']
    blk = df[(df['shot_zone']=='Restricted Area Center(C)') & (df['grouped']==' Player ')]['blk']

    fgp = df[(df['shot_zone']=='Restricted Area Center(C)') & (df['grouped']==' Player ')]['fg_perc']*100
    sfr = df[(df['shot_zone']=='Restricted Area Center(C)') & (df['grouped']==' Player ')]['shooting_foul_rate']*100
    aor = df[(df['shot_zone']=='Restricted Area Center(C)') & (df['grouped']==' Player ')]['and_one_rate']*100
    ar = df[(df['shot_zone']=='Restricted Area Center(C)') & (df['grouped']==' Player ')]['ast_rate']*100
    br = df[(df['shot_zone']=='Restricted Area Center(C)') & (df['grouped']==' Player ')]['blk_rate']*100

    data_list.append([x, y, name, diff, fgm, fga, foul, a1, ast, blk, fgp, sfr, aor, ar, br])

    # Paint (Non-RA)
    name = 'In The Paint (Non-RA)'
    theta = np.linspace(np.pi, 0, 100)
    x1 = [-80, -80, -40,-40]
    x2 = 40*np.cos(theta)
    x3 = [40, 80, 80, -80]
    y1 = [142.5, -47.5, -47.5, 0]
    y2 = 40*np.sin(theta)
    y3 = [-47.5, -47.5, 142.5, 142.5]
    x = np.concatenate((x1, x2, x3))
    y = np.concatenate((y1, y2, y3))

    comp_player = df[(df['shot_zone'].str[:21]=='In The Paint (Non-RA)') & (df['grouped']==' Player ')][comparison]*100
    comp_league = df[(df['shot_zone'].str[:21]=='In The Paint (Non-RA)') & (df['grouped']==' League ')][comparison]*100
    if len(comp_player)!=0:
        diff = ((float(comp_player)-float(comp_league))/float(comp_league))*100
    else:
        diff = 0

    fgm = df[(df['shot_zone'].str[:21]=='In The Paint (Non-RA)') & (df['grouped']==' Player ')]['fgm']
    fga = df[(df['shot_zone'].str[:21]=='In The Paint (Non-RA)') & (df['grouped']==' Player ')]['fga']
    foul = df[(df['shot_zone'].str[:21]=='In The Paint (Non-RA)') & (df['grouped']==' Player ')]['fouls']
    a1 = df[(df['shot_zone'].str[:21]=='In The Paint (Non-RA)') & (df['grouped']==' Player ')]['and_1']
    ast = df[(df['shot_zone'].str[:21]=='In The Paint (Non-RA)') & (df['grouped']==' Player ')]['ast']
    blk = df[(df['shot_zone'].str[:21]=='In The Paint (Non-RA)') & (df['grouped']==' Player ')]['blk']

    fgp = df[(df['shot_zone'].str[:21]=='In The Paint (Non-RA)') & (df['grouped']==' Player ')]['fg_perc']*100
    sfr = df[(df['shot_zone'].str[:21]=='In The Paint (Non-RA)') & (df['grouped']==' Player ')]['shooting_foul_rate']*100
    aor = df[(df['shot_zone'].str[:21]=='In The Paint (Non-RA)') & (df['grouped']==' Player ')]['and_one_rate']*100
    ar = df[(df['shot_zone'].str[:21]=='In The Paint (Non-RA)') & (df['grouped']==' Player ')]['ast_rate']*100
    br = df[(df['shot_zone'].str[:21]=='In The Paint (Non-RA)') & (df['grouped']==' Player ')]['blk_rate']*100

    data_list.append([x, y, name, diff, fgm, fga, foul, a1, ast, blk, fgp, sfr, aor, ar, br])

    # Mid-Range Right
    name = 'Mid-Range: Right'
    theta = np.linspace(0.573, 0.40, 100)
    x1 = [220, 220, 80, 80, 200]
    x2 = 237.5*np.cos(theta)
    x3 = [220]
    y1 = [87.5, -47.5, -47.5, 85, 129]
    y2 = 237.5*np.sin(theta)
    y3 = [87.5]
    x = np.concatenate((x1, x2, x3))
    y = np.concatenate((y1, y2, y3))

    comp_player = df[(df['shot_zone']=='Mid-Range Right Side(R)') & (df['grouped']==' Player ')][comparison]*100
    comp_league = df[(df['shot_zone']=='Mid-Range Right Side(R)') & (df['grouped']==' League ')][comparison]*100
    if len(comp_player)!=0:
        diff = ((float(comp_player)-float(comp_league))/float(comp_league))*100
    else:
        diff = 0

    fgm = df[(df['shot_zone']=='Mid-Range Right Side(R)') & (df['grouped']==' Player ')]['fgm']
    fga = df[(df['shot_zone']=='Mid-Range Right Side(R)') & (df['grouped']==' Player ')]['fga']
    foul = df[(df['shot_zone']=='Mid-Range Right Side(R)') & (df['grouped']==' Player ')]['fouls']
    a1 = df[(df['shot_zone']=='Mid-Range Right Side(R)') & (df['grouped']==' Player ')]['and_1']
    ast = df[(df['shot_zone']=='Mid-Range Right Side(R)') & (df['grouped']==' Player ')]['ast']
    blk = df[(df['shot_zone']=='Mid-Range Right Side(R)') & (df['grouped']==' Player ')]['blk']

    fgp = df[(df['shot_zone']=='Mid-Range Right Side(R)') & (df['grouped']==' Player ')]['fg_perc']*100
    sfr = df[(df['shot_zone']=='Mid-Range Right Side(R)') & (df['grouped']==' Player ')]['shooting_foul_rate']*100
    aor = df[(df['shot_zone']=='Mid-Range Right Side(R)') & (df['grouped']==' Player ')]['and_one_rate']*100
    ar = df[(df['shot_zone']=='Mid-Range Right Side(R)') & (df['grouped']==' Player ')]['ast_rate']*100
    br = df[(df['shot_zone']=='Mid-Range Right Side(R)') & (df['grouped']==' Player ')]['blk_rate']*100

    data_list.append([x, y, name, diff, fgm, fga, foul, a1, ast, blk, fgp, sfr, aor, ar, br])

    # Mid-Range Right Center
    name = 'Mid-Range: Right-Center'
    theta = np.linspace(1.292,0.575, 100)
    x1 = [199,80,80,50, 64]
    x2 = 237.5*np.cos(theta)
    x3 = [199]
    y1 = [129,85,142.5,142.5,221.5]
    y2 = 237.5*np.sin(theta)
    y3 = [129]
    x = np.concatenate((x1, x2, x3))
    y = np.concatenate((y1, y2, y3))

    comp_player = df[(df['shot_zone']=='Mid-Range Right Side Center(RC)') & (df['grouped']==' Player ')][comparison]*100
    comp_league = df[(df['shot_zone']=='Mid-Range Right Side Center(RC)') & (df['grouped']==' League ')][comparison]*100
    if len(comp_player)!=0:
        diff = ((float(comp_player)-float(comp_league))/float(comp_league))*100
    else:
        diff = 0

    fgm = df[(df['shot_zone']=='Mid-Range Right Side Center(RC)') & (df['grouped']==' Player ')]['fgm']
    fga = df[(df['shot_zone']=='Mid-Range Right Side Center(RC)') & (df['grouped']==' Player ')]['fga']
    foul = df[(df['shot_zone']=='Mid-Range Right Side Center(RC)') & (df['grouped']==' Player ')]['fouls']
    a1 = df[(df['shot_zone']=='Mid-Range Right Side Center(RC)') & (df['grouped']==' Player ')]['and_1']
    ast = df[(df['shot_zone']=='Mid-Range Right Side Center(RC)') & (df['grouped']==' Player ')]['ast']
    blk = df[(df['shot_zone']=='Mid-Range Right Side Center(RC)') & (df['grouped']==' Player ')]['blk']

    fgp = df[(df['shot_zone']=='Mid-Range Right Side Center(RC)') & (df['grouped']==' Player ')]['fg_perc']*100
    sfr = df[(df['shot_zone']=='Mid-Range Right Side Center(RC)') & (df['grouped']==' Player ')]['shooting_foul_rate']*100
    aor = df[(df['shot_zone']=='Mid-Range Right Side Center(RC)') & (df['grouped']==' Player ')]['and_one_rate']*100
    ar = df[(df['shot_zone']=='Mid-Range Right Side Center(RC)') & (df['grouped']==' Player ')]['ast_rate']*100
    br = df[(df['shot_zone']=='Mid-Range Right Side Center(RC)') & (df['grouped']==' Player ')]['blk_rate']*100

    data_list.append([x, y, name, diff, fgm, fga, foul, a1, ast, blk, fgp, sfr, aor, ar, br])

    # Mid-Range Center
    name = 'Mid-Range: Center'
    theta = np.linspace(1.292,1.85, 100)
    x1 = [-64,-50,50,64]
    x2 = 237.5*np.cos(theta)
    x3 = [-64]
    y1 = [221.5,142.5,142.5,221.5]
    y2 = 237.5*np.sin(theta)
    y3 = [221.5]
    x = np.concatenate((x1, x2, x3))
    y = np.concatenate((y1, y2 ,y3))

    comp_player = df[(df['shot_zone']=='Mid-Range Center(C)') & (df['grouped']==' Player ')][comparison]*100
    comp_league = df[(df['shot_zone']=='Mid-Range Center(C)') & (df['grouped']==' League ')][comparison]*100
    if len(comp_player)!=0:
        diff = ((float(comp_player)-float(comp_league))/float(comp_league))*100
    else:
        diff = 0

    fgm = df[(df['shot_zone']=='Mid-Range Center(C)') & (df['grouped']==' Player ')]['fgm']
    fga = df[(df['shot_zone']=='Mid-Range Center(C)') & (df['grouped']==' Player ')]['fga']
    foul = df[(df['shot_zone']=='Mid-Range Center(C)') & (df['grouped']==' Player ')]['fouls']
    a1 = df[(df['shot_zone']=='Mid-Range Center(C)') & (df['grouped']==' Player ')]['and_1']
    ast = df[(df['shot_zone']=='Mid-Range Center(C)') & (df['grouped']==' Player ')]['ast']
    blk = df[(df['shot_zone']=='Mid-Range Center(C)') & (df['grouped']==' Player ')]['blk']

    fgp = df[(df['shot_zone']=='Mid-Range Center(C)') & (df['grouped']==' Player ')]['fg_perc']*100
    sfr = df[(df['shot_zone']=='Mid-Range Center(C)') & (df['grouped']==' Player ')]['shooting_foul_rate']*100
    aor = df[(df['shot_zone']=='Mid-Range Center(C)') & (df['grouped']==' Player ')]['and_one_rate']*100
    ar = df[(df['shot_zone']=='Mid-Range Center(C)') & (df['grouped']==' Player ')]['ast_rate']*100
    br = df[(df['shot_zone']=='Mid-Range Center(C)') & (df['grouped']==' Player ')]['blk_rate']*100

    data_list.append([x, y, name, diff, fgm, fga, foul, a1, ast, blk, fgp, sfr, aor, ar, br])

    # Mid-Range Left Center
    name = 'Mid-Range: Left-Center'
    theta = np.linspace(1.85, 2.56675, 100)
    x1 = [-199,-80,-80,-50,-64]
    x2 = 237.5*np.cos(theta)
    x3 = [-199]
    y1 = [129,85,142.5,142.5,221.5]
    y2 = 237.5*np.sin(theta)
    y3 = [129]
    x = np.concatenate((x1, x2, x3))
    y = np.concatenate((y1, y2, y3))

    comp_player = df[(df['shot_zone']=='Mid-Range Left Side Center(LC)') & (df['grouped']==' Player ')][comparison]*100
    comp_league = df[(df['shot_zone']=='Mid-Range Left Side Center(LC)') & (df['grouped']==' League ')][comparison]*100
    if len(comp_player)!=0:
        diff = ((float(comp_player)-float(comp_league))/float(comp_league))*100
    else:
        diff = 0

    fgm = df[(df['shot_zone']=='Mid-Range Left Side Center(LC)') & (df['grouped']==' Player ')]['fgm']
    fga = df[(df['shot_zone']=='Mid-Range Left Side Center(LC)') & (df['grouped']==' Player ')]['fga']
    foul = df[(df['shot_zone']=='Mid-Range Left Side Center(LC)') & (df['grouped']==' Player ')]['fouls']
    a1 = df[(df['shot_zone']=='Mid-Range Left Side Center(LC)') & (df['grouped']==' Player ')]['and_1']
    ast = df[(df['shot_zone']=='Mid-Range Left Side Center(LC)') & (df['grouped']==' Player ')]['ast']
    blk = df[(df['shot_zone']=='Mid-Range Left Side Center(LC)') & (df['grouped']==' Player ')]['blk']

    fgp = df[(df['shot_zone']=='Mid-Range Left Side Center(LC)') & (df['grouped']==' Player ')]['fg_perc']*100
    sfr = df[(df['shot_zone']=='Mid-Range Left Side Center(LC)') & (df['grouped']==' Player ')]['shooting_foul_rate']*100
    aor = df[(df['shot_zone']=='Mid-Range Left Side Center(LC)') & (df['grouped']==' Player ')]['and_one_rate']*100
    ar = df[(df['shot_zone']=='Mid-Range Left Side Center(LC)') & (df['grouped']==' Player ')]['ast_rate']*100
    br = df[(df['shot_zone']=='Mid-Range Left Side Center(LC)') & (df['grouped']==' Player ')]['blk_rate']*100

    data_list.append([x, y, name, diff, fgm, fga, foul, a1, ast, blk, fgp, sfr, aor, ar, br])

    # Mid-Range Left
    name = 'Mid-Range: Left'
    theta = np.linspace(2.5685, 2.752, 100)
    x1 = [-220, -220, -80, -80, -199]
    x2 = 237.5*np.cos(theta)
    x3 = [-220]
    y1 = [87.5, -47.5, -47.5, 85, 129]
    y2 = 237.5*np.sin(theta)
    y3 = [87.5]
    x = np.concatenate((x1, x2))
    y = np.concatenate((y1, y2))

    comp_player = df[(df['shot_zone']=='Mid-Range Left Side(L)') & (df['grouped']==' Player ')][comparison]*100
    comp_league = df[(df['shot_zone']=='Mid-Range Left Side(L)') & (df['grouped']==' League ')][comparison]*100
    if len(comp_player)!=0:
        diff = ((float(comp_player)-float(comp_league))/float(comp_league))*100
    else:
        diff = 0

    fgm = df[(df['shot_zone']=='Mid-Range Left Side(L)') & (df['grouped']==' Player ')]['fgm']
    fga = df[(df['shot_zone']=='Mid-Range Left Side(L)') & (df['grouped']==' Player ')]['fga']
    foul = df[(df['shot_zone']=='Mid-Range Left Side(L)') & (df['grouped']==' Player ')]['fouls']
    a1 = df[(df['shot_zone']=='Mid-Range Left Side(L)') & (df['grouped']==' Player ')]['and_1']
    ast = df[(df['shot_zone']=='Mid-Range Left Side(L)') & (df['grouped']==' Player ')]['ast']
    blk = df[(df['shot_zone']=='Mid-Range Left Side(L)') & (df['grouped']==' Player ')]['blk']

    fgp = df[(df['shot_zone']=='Mid-Range Left Side(L)') & (df['grouped']==' Player ')]['fg_perc']*100
    sfr = df[(df['shot_zone']=='Mid-Range Left Side(L)') & (df['grouped']==' Player ')]['shooting_foul_rate']*100
    aor = df[(df['shot_zone']=='Mid-Range Left Side(L)') & (df['grouped']==' Player ')]['and_one_rate']*100
    ar = df[(df['shot_zone']=='Mid-Range Left Side(L)') & (df['grouped']==' Player ')]['ast_rate']*100
    br = df[(df['shot_zone']=='Mid-Range Left Side(L)') & (df['grouped']==' Player ')]['blk_rate']*100

    data_list.append([x, y, name, diff, fgm, fga, foul, a1, ast, blk, fgp, sfr, aor, ar, br])

    # 3 Point Right Corner
    name = 'Corner 3: Right'
    x = [250,220, 220, 250, 250]
    y = [87.5,87.5,-47.5,-47.5, 87.5]

    comp_player = df[(df['shot_zone']=='Right Corner 3 Right Side(R)') & (df['grouped']==' Player ')][comparison]*100
    comp_league = df[(df['shot_zone']=='Right Corner 3 Right Side(R)') & (df['grouped']==' League ')][comparison]*100
    if len(comp_player)!=0:
        diff = ((float(comp_player)-float(comp_league))/float(comp_league))*100
    else:
        diff = 0

    fgm = df[(df['shot_zone']=='Right Corner 3 Right Side(R)') & (df['grouped']==' Player ')]['fgm']
    fga = df[(df['shot_zone']=='Right Corner 3 Right Side(R)') & (df['grouped']==' Player ')]['fga']
    foul = df[(df['shot_zone']=='Right Corner 3 Right Side(R)') & (df['grouped']==' Player ')]['fouls']
    a1 = df[(df['shot_zone']=='Right Corner 3 Right Side(R)') & (df['grouped']==' Player ')]['and_1']
    ast = df[(df['shot_zone']=='Right Corner 3 Right Side(R)') & (df['grouped']==' Player ')]['ast']
    blk = df[(df['shot_zone']=='Right Corner 3 Right Side(R)') & (df['grouped']==' Player ')]['blk']

    fgp = df[(df['shot_zone']=='Right Corner 3 Right Side(R)') & (df['grouped']==' Player ')]['fg_perc']*100
    sfr = df[(df['shot_zone']=='Right Corner 3 Right Side(R)') & (df['grouped']==' Player ')]['shooting_foul_rate']*100
    aor = df[(df['shot_zone']=='Right Corner 3 Right Side(R)') & (df['grouped']==' Player ')]['and_one_rate']*100
    ar = df[(df['shot_zone']=='Right Corner 3 Right Side(R)') & (df['grouped']==' Player ')]['ast_rate']*100
    br = df[(df['shot_zone']=='Right Corner 3 Right Side(R)') & (df['grouped']==' Player ')]['blk_rate']*100

    data_list.append([x, y, name, diff, fgm, fga, foul, a1, ast, blk, fgp, sfr, aor, ar, br])

    # 3 Point Above the Break Right
    name = 'Above the Break 3: Right'
    theta = np.linspace(1.25, 0.39,100)
    x1 = [220,250,250,100.5,75]
    x2 = 237.5*np.cos(theta)
    x3 = [220]
    y1 = [87.5,87.5,422.5,422.5,226]
    y2 = 237.5*np.sin(theta)
    y3 = [87.5]
    x = np.concatenate((x1, x2, x3))
    y = np.concatenate((y1, y2, y3))

    comp_player = df[(df['shot_zone']=='Above the Break 3 Right Side Center(RC)') & (df['grouped']==' Player ')][comparison]*100
    comp_league = df[(df['shot_zone']=='Above the Break 3 Right Side Center(RC)') & (df['grouped']==' League ')][comparison]*100
    if len(comp_player)!=0:
        diff = ((float(comp_player)-float(comp_league))/float(comp_league))*100
    else:
        diff = 0

    fgm = df[(df['shot_zone']=='Above the Break 3 Right Side Center(RC)') & (df['grouped']==' Player ')]['fgm']
    fga = df[(df['shot_zone']=='Above the Break 3 Right Side Center(RC)') & (df['grouped']==' Player ')]['fga']
    foul = df[(df['shot_zone']=='Above the Break 3 Right Side Center(RC)') & (df['grouped']==' Player ')]['fouls']
    a1 = df[(df['shot_zone']=='Above the Break 3 Right Side Center(RC)') & (df['grouped']==' Player ')]['and_1']
    ast = df[(df['shot_zone']=='Above the Break 3 Right Side Center(RC)') & (df['grouped']==' Player ')]['ast']
    blk = df[(df['shot_zone']=='Above the Break 3 Right Side Center(RC)') & (df['grouped']==' Player ')]['blk']

    fgp = df[(df['shot_zone']=='Above the Break 3 Right Side Center(RC)') & (df['grouped']==' Player ')]['fg_perc']*100
    sfr = df[(df['shot_zone']=='Above the Break 3 Right Side Center(RC)') & (df['grouped']==' Player ')]['shooting_foul_rate']*100
    aor = df[(df['shot_zone']=='Above the Break 3 Right Side Center(RC)') & (df['grouped']==' Player ')]['and_one_rate']*100
    ar = df[(df['shot_zone']=='Above the Break 3 Right Side Center(RC)') & (df['grouped']==' Player ')]['ast_rate']*100
    br = df[(df['shot_zone']=='Above the Break 3 Right Side Center(RC)') & (df['grouped']==' Player ')]['blk_rate']*100

    data_list.append([x, y, name, diff, fgm, fga, foul, a1, ast, blk, fgp, sfr, aor, ar, br])

    # 3 Point Above the Break Center
    name = 'Above the Break 3: Center'
    theta = np.linspace(1.25,1.8915, 100)
    x1 = [-75,-100.5,100.5,75]
    x2 = 237.5*np.cos(theta)
    x3 = [-75]
    y1 = [226,422.5,422.5,226]
    y2 = 237.5*np.sin(theta)
    y3 = [226]
    x = np.concatenate((x1, x2, x3))
    y = np.concatenate((y1, y2, y3))

    comp_player = df[(df['shot_zone']=='Above the Break 3 Center(C)') & (df['grouped']==' Player ')][comparison]*100
    comp_league = df[(df['shot_zone']=='Above the Break 3 Center(C)') & (df['grouped']==' League ')][comparison]*100
    if len(comp_player)!=0:
        diff = ((float(comp_player)-float(comp_league))/float(comp_league))*100
    else:
        diff = 0

    fgm = df[(df['shot_zone']=='Above the Break 3 Center(C)') & (df['grouped']==' Player ')]['fgm']
    fga = df[(df['shot_zone']=='Above the Break 3 Center(C)') & (df['grouped']==' Player ')]['fga']
    foul = df[(df['shot_zone']=='Above the Break 3 Center(C)') & (df['grouped']==' Player ')]['fouls']
    a1 = df[(df['shot_zone']=='Above the Break 3 Center(C)') & (df['grouped']==' Player ')]['and_1']
    ast = df[(df['shot_zone']=='Above the Break 3 Center(C)') & (df['grouped']==' Player ')]['ast']
    blk = df[(df['shot_zone']=='Above the Break 3 Center(C)') & (df['grouped']==' Player ')]['blk']

    fgp = df[(df['shot_zone']=='Above the Break 3 Center(C)') & (df['grouped']==' Player ')]['fg_perc']*100
    sfr = df[(df['shot_zone']=='Above the Break 3 Center(C)') & (df['grouped']==' Player ')]['shooting_foul_rate']*100
    aor = df[(df['shot_zone']=='Above the Break 3 Center(C)') & (df['grouped']==' Player ')]['and_one_rate']*100
    ar = df[(df['shot_zone']=='Above the Break 3 Center(C)') & (df['grouped']==' Player ')]['ast_rate']*100
    br = df[(df['shot_zone']=='Above the Break 3 Center(C)') & (df['grouped']==' Player ')]['blk_rate']*100

    data_list.append([x, y, name, diff, fgm, fga, foul, a1, ast, blk, fgp, sfr, aor, ar, br])

    # 3 Point Above the Break Left
    name = 'Above the Break 3: Left'
    theta = np.linspace(1.892, 2.75,100)
    x1 = [-220,-250,-250,-100.5,-75]
    x2 = 237.5*np.cos(theta)
    x3 = [-220]
    y1 = [87.5,87.5,422.5,422.5,226]
    y2 = 237.5*np.sin(theta)
    y3 = [87.5]
    x = np.concatenate((x1, x2, x3))
    y = np.concatenate((y1, y2, y3))

    comp_player = df[(df['shot_zone']=='Above the Break 3 Left Side Center(LC)') & (df['grouped']==' Player ')][comparison]*100
    comp_league = df[(df['shot_zone']=='Above the Break 3 Left Side Center(LC)') & (df['grouped']==' League ')][comparison]*100
    if len(comp_player)!=0:
        diff = ((float(comp_player)-float(comp_league))/float(comp_league))*100
    else:
        diff = 0

    fgm = df[(df['shot_zone']=='Above the Break 3 Left Side Center(LC)') & (df['grouped']==' Player ')]['fgm']
    fga = df[(df['shot_zone']=='Above the Break 3 Left Side Center(LC)') & (df['grouped']==' Player ')]['fga']
    foul = df[(df['shot_zone']=='Above the Break 3 Left Side Center(LC)') & (df['grouped']==' Player ')]['fouls']
    a1 = df[(df['shot_zone']=='Above the Break 3 Left Side Center(LC)') & (df['grouped']==' Player ')]['and_1']
    ast = df[(df['shot_zone']=='Above the Break 3 Left Side Center(LC)') & (df['grouped']==' Player ')]['ast']
    blk = df[(df['shot_zone']=='Above the Break 3 Left Side Center(LC)') & (df['grouped']==' Player ')]['blk']

    fgp = df[(df['shot_zone']=='Above the Break 3 Left Side Center(LC)') & (df['grouped']==' Player ')]['fg_perc']*100
    sfr = df[(df['shot_zone']=='Above the Break 3 Left Side Center(LC)') & (df['grouped']==' Player ')]['shooting_foul_rate']*100
    aor = df[(df['shot_zone']=='Above the Break 3 Left Side Center(LC)') & (df['grouped']==' Player ')]['and_one_rate']*100
    ar = df[(df['shot_zone']=='Above the Break 3 Left Side Center(LC)') & (df['grouped']==' Player ')]['ast_rate']*100
    br = df[(df['shot_zone']=='Above the Break 3 Left Side Center(LC)') & (df['grouped']==' Player ')]['blk_rate']*100

    data_list.append([x, y, name, diff, fgm, fga, foul, a1, ast, blk, fgp, sfr, aor, ar, br])

    # 3 Point Left Corner
    name = 'Corner 3: Left'
    x = [-250,-220, -220, -250, -250]
    y = [87.5,87.5,-47.5,-47.5, 87.5]

    comp_player = df[(df['shot_zone']=='Left Corner 3 Left Side(L)') & (df['grouped']==' Player ')][comparison]*100
    comp_league = df[(df['shot_zone']=='Left Corner 3 Left Side(L)') & (df['grouped']==' League ')][comparison]*100
    if len(comp_player)!=0:
        diff = ((float(comp_player)-float(comp_league))/float(comp_league))*100
    else:
        diff = 0

    fgm = df[(df['shot_zone']=='Left Corner 3 Left Side(L)') & (df['grouped']==' Player ')]['fgm']
    fga = df[(df['shot_zone']=='Left Corner 3 Left Side(L)') & (df['grouped']==' Player ')]['fga']
    foul = df[(df['shot_zone']=='Left Corner 3 Left Side(L)') & (df['grouped']==' Player ')]['fouls']
    a1 = df[(df['shot_zone']=='Left Corner 3 Left Side(L)') & (df['grouped']==' Player ')]['and_1']
    ast = df[(df['shot_zone']=='Left Corner 3 Left Side(L)') & (df['grouped']==' Player ')]['ast']
    blk = df[(df['shot_zone']=='Left Corner 3 Left Side(L)') & (df['grouped']==' Player ')]['blk']

    fgp = df[(df['shot_zone']=='Left Corner 3 Left Side(L)') & (df['grouped']==' Player ')]['fg_perc']*100
    sfr = df[(df['shot_zone']=='Left Corner 3 Left Side(L)') & (df['grouped']==' Player ')]['shooting_foul_rate']*100
    aor = df[(df['shot_zone']=='Left Corner 3 Left Side(L)') & (df['grouped']==' Player ')]['and_one_rate']*100
    ar = df[(df['shot_zone']=='Left Corner 3 Left Side(L)') & (df['grouped']==' Player ')]['ast_rate']*100
    br = df[(df['shot_zone']=='Left Corner 3 Left Side(L)') & (df['grouped']==' Player ')]['blk_rate']*100

    data_list.append([x, y, name, diff, fgm, fga, foul, a1, ast, blk, fgp, sfr, aor, ar, br])

    data_source = ColumnDataSource(pd.DataFrame(data_list, columns=["X", "Y", "AREA", "PERC_DIFF", "MADE", "TOTAL",
                                                                    "FOULS", "AND_1", "ASSISTED", "BLOCKED", "PERC_FG",
                                                                    "PERC_SF", "PERC_A1", "PERC_AST", "PERC_BLK"]))

    return data_source

def update_player(attrname, old, new):
    # Get Current Values
    player = player_select.value
    player_new_id = player_dict[player].get('player_id')
    season_new = get_seasons(cursor, cxn, seasons_query, player_new_id)
    season_select.options = season_new
    season_select.value = season_new[0]
    comparison_val = comp_dict[comparison_select.value]
    fig.title.text = player + " " + season_select.value + " Shot Chart: " + comparison_select.value
    df = get_data(cursor, cxn, data_cube_summary, season_select.value, player_new_id)
    src = summary(df, comparison_val)
    source.data.update(src.data)

def update_season(attrname, old, new):
    # Get Current Values
    player = player_dict[player_select.value].get('player_id')
    comparison_val = comp_dict[comparison_select.value]
    fig.title.text = player_select.value + " " + season_select.value + " Shot Chart: " + comparison_select.value
    df = get_data(cursor, cxn, data_cube_summary, season_select.value, player)
    src = summary(df, comparison_val)
    source.data.update(src.data)

def update_comparison(attrname, old, new):
    # Get Current Values
    player = player_dict[player_select.value].get('player_id')
    comparison_val = comp_dict[comparison_select.value]
    fig.title.text = player_select.value + " " + season_select.value + " Shot Chart: " + comparison_select.value
    df = get_data(cursor, cxn, data_cube_summary, season_select.value, player)
    src = summary(df, comparison_val)
    source.data.update(src.data)

# Connect to database
cxn = mysql.connector.connect(**config_info)
cursor = cxn.cursor()
try:
    cursor.execute("USE {}".format(db_name))
    print("Connected to database {}".format(db_name))
except mysql.connector.Error as err:
    print("Database {} does not exist.".format(db_name))
    if err.errno == errorcode.ER_BAD_DB_ERROR:
        create_database(cursor)
        print("Database {} created successfully.".format(db_name))
        cnx.database = db_name
    else:
        print(err)
        exit(1)

player = 'LeBron James'
# Set Initial Values for Drop Downs
# Player select drop down
player_dict = get_players(cursor, cxn, player_query)
player_select = Select(value=player, title='Player:', options=sorted(player_dict.keys()), width=250)
player_select_id = player_dict[player_select.value].get('player_id')

# Season select drop down
season_list = get_seasons(cursor, cxn, seasons_query, player_select_id)
season_select = Select(value=season_list[-1], title='Season:', options=season_list, width=250)

# Comparison select drop down
comparison_select = Select(value='Field Goal Percentage', title='Comparison:', options=(list(comp_dict.keys())), width=250)

conditions=(season_select.value, player_select_id)

# Get data frame
df = get_data(cursor, cxn, data_cube_summary, season_select.value, player_select_id)

# Get data_source
source = summary(df)
print(source)
fig = bokeh_shot_chart(source, player_select.value + " " + season_select.value + " Shot Chart: " + comparison_select.value)

player_select.on_change('value', update_player)
season_select.on_change('value', update_season)
comparison_select.on_change('value', update_comparison)

controls=column(player_select, season_select, comparison_select)
curdoc().add_root(row(controls, fig))
curdoc().title = 'NBA Shot Charts'
