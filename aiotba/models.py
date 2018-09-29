import datetime


class Field:
    """base field class, also appropriate for primitives that the json module already converts like int/float/bool/str"""
    repr_str = ""

    def __init__(self, *args, **kwargs):
        pass

    def __repr__(self):
        cls = self.__class__
        return f"<{cls.__module__}.{cls.__qualname__}: " + self.repr_str.format(s=self) + ">"


    def convert(self, value):
        return value


class Array(Field):
    def __init__(self, type_):
       self.cls = type_.__class__

    def convert(self, value):
        return [self.cls().convert(v) for v in value]

    """mostly for ide purposes?"""
    def __getitem__(self, item):
        return self.cls


class Dict(Field):
    """used for coercing trees or things with variable keys, don't use to passthru dicts"""
    def __init__(self, key_type, value_type):
        self.key_type = key_type.__class__
        self.value_type = value_type.__class__

    def convert(self, value):
        return {self.key_type().convert(k): self.value_type.convert(v) for k, v in value.items()}


class Timestamp(Field):
    def __init__(self, fmt="%Y-%m-%d %H:%M:%S %z"):
        self.fmt = fmt

    def convert(self, value):
        if self.fmt != "unix":
            return datetime.datetime.strptime(value, self.fmt)
        else:
            return datetime.datetime.fromtimestamp(value)


class HomeChampionship(Field):
    def convert(self, value):
        return {int(k): v for k, v in value.items()} if value else {}


class ModelType(type):
    def __new__(mcs, name, bases, attrs):
        inst = super().__new__(mcs, name, bases, attrs)
        inst.__map__ = {}

        # pull in base class maps
        for base in bases:
            if hasattr(base, "__map__"):
                inst.__map__.update(base.__map__)

        for attr_name, attr_value in attrs.items():
            if isinstance(attr_value, Field):
                inst.__map__[attr_name] = attr_value

        return inst


class Model(Field, metaclass=ModelType):
    __prefix__ = ""

    def convert(self, data):
        cutoff = len(self.__prefix__)
        self._data = data
        for field_name, converter in self.__map__.items():
            setattr(self, field_name, converter.convert(data[field_name[cutoff:]]))

        return self

    def __contains__(self, item):
        return item in self.__map__

    def __getitem__(self, key):
        if key not in self:
            raise KeyError(key)
        return getattr(self, key)


class APIStatus(Model):
    """TBA API Status"""
    class Web(Model):
        """a field returned by APIStatus"""
        commit_time = Timestamp()
        current_commit = Field(str)
        deploy_time = Field(str) # the timestamp is unorthodox and can't be parsed by datetime
        travis_job = Field(str) # a string for some reason

    class AppVersion(Model):
        min_app_version = Field(int)
        latest_app_version = Field(int)

    current_season = Field(int)
    max_season = Field(int)
    is_datafeed_down = Field(bool)
    down_events = Array(Field(str))
    ios = AppVersion()
    android = AppVersion()

    # questionable but the tba api has it so here we are
    contbuild_enabled = Field()
    web = Web()


class TeamSimple(Model):
    key = Field(str)
    team_number = Field(int)
    nickname = Field(str)
    name = Field(str)
    city = Field(str)
    state_prov = Field(str)
    country = Field(str)


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
    address = Field(str)
    postal_code = Field(str)
    gmaps_place_id = Field(str)
    gmaps_url = Field(str)
    lat = Field(float)
    lng = Field(float)
    location_name = Field(str)
    website = Field(str)
    rookie_year = Field(int)
    motto = Field(str)
    home_championship = HomeChampionship()

    repr_str = "{s.team_number} {s.nickname}"
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
    """
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
    """
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
    year = Field(int)


