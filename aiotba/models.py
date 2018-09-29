import datetime
from typing import Dict, Tuple, List, Union, Any



class Converter:
    repr_str = "{hex(id(s))"

    def __repr__(self):
        cls = self.__class__
        return f"<{cls.__module__}.{cls.__qualname__}: " + self.repr_str.format(s=self) + ">"


class Timestamp(Converter):
    def __init__(self, fmt="%Y-%m-%d %H:%M:%S %z"):
        self.fmt = fmt

    def convert(self, value):
        if self.fmt != "unix":
            return datetime.datetime.strptime(value, self.fmt)
        else:
            return datetime.datetime.fromtimestamp(value)


class HomeChampionship(Converter):
    def __call__(self, value):
        return {int(k): v for k, v in value.items()} if value else {}


class Model(Converter):
    __prefix__ = ""

    def __init__(self, data):

        cutoff = len(self.__prefix__)
        #self._data = data

        # base classes annotations should be incorporated into the list of fields
        fields = dict(self.__annotations__)
        for base in self.__class__.__bases__:
            if hasattr(base, "__annotations__"):
                fields.update(base.__annotations__)

        for field_name, field_type in fields.items():
            print(field_name)
            # some checks here
            setattr(self, field_name, to_model(data[field_name[cutoff:]], field_type))

    def __contains__(self, item):
        return item in self.__annotations__

    def __getitem__(self, key):
        if key not in self:
            raise KeyError(key)
        return getattr(self, key)


class APIStatus(Model):
    """TBA API Status"""
    class Web(Model):
        """a field returned by APIStatus"""
        commit_time: Timestamp()
        current_commit: str
        deploy_time: str # the timestamp is unorthodox and can't be parsed by datetime
        travis_job: str # a string for some reason

    class AppVersion(Model):
        min_app_version: int
        latest_app_version: int

    current_season: int
    max_season: int
    is_datafeed_down: bool
    down_events: List[str]
    ios: AppVersion
    android: AppVersion

    # questionable but the tba api has it so here we are
    contbuild_enabled: str
    web: Web


class TeamSimple(Model):
    key: str
    team_number: int
    nickname: str
    name: str
    city: str
    state_prov: str
    country: str


class Team(TeamSimple):
    """
    key = Field()
    team_number = Field()
    nickname = Field()
    name = Field()
    city = Field()
    state_prov = Field()
    country = Field()
    """
    # these are supposedly NULL, mostly
    address: str
    postal_code: str
    gmaps_place_id: str
    gmaps_url: str

    # these would be floats but they get nulled LOL
    lat: str
    lng: str
    location_name: str
    website: str

    # due to a limitation in TBA's API, rookie_year isn't always available; other methods are needed to determine
    # rookie year for certain teams, such as iterating over their seasons. Here, we just set it to zero if we see None.
    rookie_year: lambda d: int(d) if d else 0
    motto: str
    home_championship = HomeChampionship()

    repr_str = "{s.team_number} {s.nickname}"
"""
class TeamRobot(Model):
    year = Field(int)
    robot_name = Field(str)
    key = Field(str)
    team_key = Field(str)


class District(Model):
    abbreviation = Field(str)
    display_name = Field(str)
    key = Field(str)
    year = Field(int)


DistrictList = District # in line with API doc name


class EventSimple(Model):
    key = Field(str)
    name = Field(str)
    event_code = Field(str)
    event_type = Field(int)
    district = District()
    city = Field(str)
    state_prov = Field(str)
    country = Field(str)
    start_date = Timestamp(fmt="%Y-%m-%d")
    end_date = Timestamp(fmt="%Y-%m-%d")
    year = Field(int)


class Webcast(Model):
    type = Field(str)
    channel = Field(str)
    file = Field(str)


class Event(EventSimple):
    ""
    key = Field()
    name = Field()
    event_code = Field()
    event_type = Field()
    district = District()
    city = Field()
    state_prov = Field()
    country = Field()
    start_date = Timestamp(fmt="%Y-%m-%d")
    end_date = Timestamp(fmt="%Y-%m-%d")
    year = Field()
    ""
    short_name = Field(str)
    event_type_string = Field(str)
    week = Field(int)
    address = Field(str)
    postal_code = Field(str)
    gmaps_place_id = Field(str)
    gmaps_url = Field(str)
    lat = Field(float)
    lng = Field(float)
    location_name = Field(str)
    timezone = Field(str)
    website = Field(str)
    first_event_id = Field(str)
    first_event_code = Field(str)
    webcasts = Array(Webcast())
    division_keys = Array(Field(str))
    parent_event_key = Field(str)
    playoff_type = Field(int)
    playoff_type_string = Field(str)


class WLTRecord(Model):
    losses = Field(int)
    wins = Field(int)
    ties = Field(int)


class ValueInfo(Model):
    name = Field(str)
    precision = Field(int)


class RankingEntry(Model):
    dq = Field(int)
    matches_played = Field(int)
    qual_average = Field(float)
    rank = Field(int)
    record = WLTRecord()
    sort_orders = Array(Field(float))
    team_key = Field(str)


class BackupTeam(Model):
    __prefix__ = "team_"
    team_out = Field(str)
    team_in = Field(str)


class PlayoffStatus(Model):
    level = Field(str)
    current_level_record = WLTRecord()
    record = WLTRecord()
    status = Field(str)
    playoff_average = Field(int)


class TeamEventStatus(Model):
    class RankStatus(Model):

        num_teams = Field(int)
        ranking = RankingEntry()
        sort_order_info = Array(ValueInfo())
        status = Field(str)

    class AllianceStatus(Model):
        name = Field(str)
        number = Field(int)
        backup = BackupTeam()
        pick = Field(int)

    qual = RankStatus()
    alliance = AllianceStatus(str)
    playoff = PlayoffStatus()
    alliance_status_str = Field(str)
    playoff_status_str = Field(str)
    overall_status_str = Field(str)
    next_match_key = Field(str)
    last_match_key = Field(str)


class EventRanking(Model):
    class EventRankingEntry(RankingEntry):
        extra_stats = Array(Field(float))
    rankings = Array(EventRankingEntry())
    extra_stats_info = Array(ValueInfo())
    sort_order_info = Array(ValueInfo())


class EventDistrictPoints(Model):
    class DistrictPointsData(Model):
        alliance_points = Field(int)
        award_points = Field(int)
        qual_points = Field(int)
        elim_points = Field(int)
        total = Field(int)

    class TiebreakerData(Model):
        highest_qual_scores = Array(Field(int))
        qual_wins = Field(int)

    points = Dict(Field(str), DistrictPointsData())
    tiebreakers = Dict(Field(str), TiebreakerData())


class EventInsights(Model):
    # heck no i don't want to maintain this every year :(
    qual = Field(dict)
    playoff = Field(dict)


class EventOPRs(Model):
    oprs = Field(dict)
    dprs = Field(dict)
    ccwms = Field(dict)


EventPredictions = Field # year specific, no documented API


class MatchAlliance(Model):
    score = Field(int)
    team_keys = Array(Field(str))
    surrogate_team_keys = Array(Field(str))
    dq_team_keys = Array(Field(str))


class MatchSimple(Model):
    key = Field(str)
    comp_level = Field(str)
    set_number = Field(int)
    match_number = Field(int)
    alliances = Dict(Field(str), MatchAlliance())
    winning_alliance = Field(str)
    event_key = Field(str)
    time = Timestamp(fmt="unix")
    predicted_time = Timestamp(fmt="unix")
    actual_time = Timestamp(fmt="unix")


class Match(MatchSimple):
    class Video(Model):
        key = Field(str)
        type = Field(str)

    post_result_time = Timestamp(fmt="unix")
    score_breakdown = Field(dict) # aw hell naw
    videos = Array(Video())


class Media(Model):
    key = Field(str)
    type = Field(str)
    foreign_key = Field(str)
    details = Field(dict)
    preferred = Field(bool)


class EliminationAlliance(Model):
    name = Field(str)
    backup = BackupTeam()
    declines = Array(Field(str))
    picks = Array(Field(str))
    status = PlayoffStatus()


class AwardRecipient(Model):
    team_key = Field(str)
    awardee = Field(str)


class Award(Model):
    name = Field(str)
    award_type = Field(int)
    event_key = Field(str)
    recipient_list = Array(AwardRecipient())
    year = Field(int)"""


def to_model(data, model):
    if model is Any:
        return data # don't even touch it
    elif model is str:
        return data if data else ""  # sometimes fields are None, so we return an empty string for type consistency

    if hasattr(model, "__origin__"):
        # this is a ghetto check for things like List[int] or smth
        # duck typing amirite
        if model.__origin__ == list:
            return [to_model(d, model.__args__[0]) for d in data]
        elif model.__origin__ == dict:
            return {to_model(k, model.__args__[0]): to_model(v, model.__args__[1]) for k, v in data.items()}

    # usually you can just call otherwise lol
    return model(data)

