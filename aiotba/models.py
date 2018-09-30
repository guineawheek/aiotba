import datetime
from typing import Dict, Tuple, List, Union, Any


class Converter:
    repr_str = ""

    def __repr__(self):
        cls = self.__class__
        return f"<{cls.__module__}.{cls.__qualname__}" + self.repr_str.format(s=self) + ">"


class Timestamp(Converter):
    def __init__(self, fmt="%Y-%m-%d %H:%M:%S %z"):
        self.fmt = fmt

    def __call__(self, value) -> datetime.datetime:
        if self.fmt != "unix":
            return datetime.datetime.strptime(value, self.fmt)
        else:
            return datetime.datetime.fromtimestamp(value)


class HomeChampionship(Converter):
    def __call__(self, value) -> Dict[int, str]:
        return {int(k): v for k, v in value.items()} if value else {}


class Model(Converter):
    __prefix__ = ""

    def __init__(self, data):

        cutoff = len(self.__prefix__)
        # self._data = data

        # base classes annotations should be incorporated into the list of fields
        fields = dict(self.__annotations__)
        for base in self.__class__.__bases__:
            if hasattr(base, "__annotations__"):
                fields.update(base.__annotations__)

        for field_name, field_type in fields.items():
            try:
                if field_name[cutoff:] in data:
                    setattr(self, field_name, to_model(data[field_name[cutoff:]], field_type))
                else:
                    setattr(self, field_name, None)
            except TypeError:
                print(f"REEEEEEE: {field_name}")
                raise

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
    home_championship: HomeChampionship()

    repr_str = ": {s.team_number} {s.nickname}"


class TeamRobot(Model):
    year: int
    robot_name: str
    key: str
    team_key: str


class District(Model):
    abbreviation: str
    display_name: str
    key: str
    year: int


DistrictList = District  # in line with API doc name


class EventSimple(Model):
    key: str
    name: str
    event_code: str
    event_type: int
    district: District  # nullable
    city: str
    state_prov: str
    country: str
    start_date: Timestamp(fmt="%Y-%m-%d")
    end_date: Timestamp(fmt="%Y-%m-%d")
    year: int


class Webcast(Model):
    type: str
    channel: str
    file: str


class Event(EventSimple):
    short_name: str
    event_type_string: str
    week: int
    address: str
    postal_code: str
    gmaps_place_id: str
    gmaps_url: str
    lat: str
    lng: str
    location_name: str
    timezone: str
    website: str
    first_event_id: str
    first_event_code: str
    webcasts: List[Webcast]
    division_keys: List[str]
    parent_event_key: str
    playoff_type: int
    playoff_type_string: str

    repr_str = ": {s.name}"

class WLTRecord(Model):
    losses: int
    wins: int
    ties: int


class ValueInfo(Model):
    name: str
    precision: int


class RankingEntry(Model):
    dq: int
    matches_played: int
    qual_average: float
    rank: int
    record: WLTRecord
    sort_orders: List[float]
    team_key: str


class BackupTeam(Model):
    __prefix__ = "team_"
    team_out: str
    team_in: str


class PlayoffStatus(Model):
    level: str
    current_level_record: WLTRecord
    record: WLTRecord
    status: str
    playoff_average: int


class TeamEventStatus(Model):
    class RankStatus(Model):
        num_teams: int
        ranking: RankingEntry
        sort_order_info: List[ValueInfo]
        status: str

    class AllianceStatus(Model):
        name: str
        number: int
        backup: BackupTeam
        pick: int

    qual: RankStatus
    alliance: AllianceStatus
    playoff: PlayoffStatus
    alliance_status_str: str
    playoff_status_str: str
    overall_status_str: str
    next_match_key: str
    last_match_key: str


class EventRankings(Model):
    class EventRankingEntry(RankingEntry):
        extra_stats: List[float]
    rankings: List[EventRankingEntry]
    extra_stats_info: List[ValueInfo]
    sort_order_info: List[ValueInfo]


class EventDistrictPoints(Model):
    class DistrictPointsData(Model):
        alliance_points: int
        award_points: int
        qual_points: int
        elim_points: int
        total: int

    class TiebreakerData(Model):
        highest_qual_scores: List[int]
        qual_wins: int

    points: Dict[str, DistrictPointsData]
    tiebreakers: Dict[str, TiebreakerData]


class EventInsights(Model):
    # heck no i don't want to maintain this every year :(
    qual: dict
    playoff: dict


class EventOPRs(Model):
    oprs: Dict[str, float]
    dprs: Dict[str, float]
    ccwms: Dict[str, float]


EventPredictions = dict  # year specific, no documented API


class DistrictRanking(Model):
    class DistrictEventPoints(EventDistrictPoints.DistrictPointsData):
        event_key: str
        district_cmp: bool
    team_key: str
    rank: int
    rookie_bonus: int
    point_total: int
    event_points: List[DistrictEventPoints]


class MatchAlliance(Model):
    score: int
    team_keys: List[str]
    surrogate_team_keys: List[str]
    dq_team_keys: List[str]


class MatchSimple(Model):
    key: str
    comp_level: str
    set_number: int
    match_number: int
    alliances: Dict[str, MatchAlliance]
    winning_alliance: str
    event_key: str
    time: Timestamp(fmt="unix")
    predicted_time: Timestamp(fmt="unix")
    actual_time: Timestamp(fmt="unix")


class Match(MatchSimple):
    class Video(Model):
        key: str
        type: str

    post_result_time: Timestamp(fmt="unix")
    score_breakdown: dict # aw hell naw
    videos: List[Video]


class Media(Model):
    key: str
    type: str
    foreign_key: str
    details: dict
    preferred: bool


class EliminationAlliance(Model):
    name: str
    backup: BackupTeam
    declines: List[str]
    picks: List[str]
    status: PlayoffStatus


class AwardRecipient(Model):
    team_key: str
    awardee: str


class Award(Model):
    name: str
    award_type: int
    event_key: str
    recipient_list: List[AwardRecipient]
    year: int


def to_model(data, model):
    if model is Any:
        return data # don't even touch it

    # this is a ghetto check for things like List[int] or smth
    # duck typing amirite
    if hasattr(model, "__origin__"):

        # the in expr is for 3.6 compat REEEEEEEEEEEEEEEE
        if model.__origin__ in (list, List):
            return [to_model(d, model.__args__[0]) for d in data]
        elif model.__origin__ in (dict, Dict):
            return {to_model(k, model.__args__[0]): to_model(v, model.__args__[1]) for k, v in data.items()}

    # usually you can just call otherwise lol
    # if the data endpoint is None, chances are calling a model on it will fail, so we can just return None
    return model(data) if data is not None else None

