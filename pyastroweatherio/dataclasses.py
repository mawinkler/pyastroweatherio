"""Defines the Data Classes used."""
import logging
from datetime import datetime
from datetime import timedelta

from pyastroweatherio.const import CLOUDCOVER_PLAIN
from pyastroweatherio.const import CONDITION
from pyastroweatherio.const import DEEP_SKY_THRESHOLD
from pyastroweatherio.const import LIFTED_INDEX_PLAIN
from pyastroweatherio.const import RH2M_PLAIN
from pyastroweatherio.const import SEEING_PLAIN
from pyastroweatherio.const import TRANSPARENCY_PLAIN
from pyastroweatherio.const import WIND10M_SPEED_PLAIN

_LOGGER = logging.getLogger(__name__)


class ForecastData:
    """A representation of 3-Hour Based Forecast AstroWeather Data."""

    def __init__(self, data):
        self._product = data["product"]
        self._init = data["init"]
        self._timepoint = data["timepoint"]
        self._latitude = data["latitude"]
        self._longitude = data["longitude"]
        self._cloudcover = data["init"]
        self._timepoint = data["timepoint"]
        self._cloudcover = data["cloudcover"]
        self._seeing = data["seeing"]
        self._transparency = data["transparency"]
        self._lifted_index = data["lifted_index"]
        self._rh2m = data["rh2m"]
        self._wind10m = data["wind10m"]
        self._temp2m = data["temp2m"]
        self._prec_type = data["prec_type"]
        self._forecast = data["forecast"]

    @property
    def product(self) -> int:
        """Return Forecast Product Type."""
        return self._product

    @property
    def init(self) -> datetime:
        """Return Forecast Anchor."""
        return self._init

    @property
    def timepoint(self) -> int:
        """Return Forecast Hour."""
        return self._timepoint

    @property
    def latitude(self) -> float:
        """Return Forecast Hour."""
        return self._latitude

    @property
    def longitude(self) -> float:
        """Return Forecast Hour."""
        return self._longitude

    @property
    def timestamp(self) -> datetime:
        """Return Data Timestamp."""
        return self._init + timedelta(hours=self._timepoint)

    @property
    def cloudcover(self) -> int:
        """Return Cloud Coverage."""
        return self._cloudcover

    @property
    def cloudcover_plain(self) -> str:
        """Return Cloud Coverage."""
        return CLOUDCOVER_PLAIN[self._cloudcover - 1]

    @property
    def seeing(self) -> int:
        """Return Seeing."""
        return self._seeing

    @property
    def seeing_plain(self) -> str:
        """Return Seeing."""
        return SEEING_PLAIN[self._seeing - 1]

    @property
    def transparency(self) -> int:
        """Return Transparency."""
        return self._transparency

    @property
    def transparency_plain(self) -> str:
        """Return Transparency."""
        return TRANSPARENCY_PLAIN[self._transparency - 1]

    @property
    def lifted_index(self) -> int:
        """Return Lifted Index."""
        return self._lifted_index

    @property
    def lifted_index_plain(self) -> str:
        """Return Lifted Index."""

        trans = {
            -10: LIFTED_INDEX_PLAIN[0],
            -6: LIFTED_INDEX_PLAIN[1],
            -4: LIFTED_INDEX_PLAIN[2],
            -1: LIFTED_INDEX_PLAIN[3],
            2: LIFTED_INDEX_PLAIN[4],
            6: LIFTED_INDEX_PLAIN[5],
            10: LIFTED_INDEX_PLAIN[6],
            15: LIFTED_INDEX_PLAIN[7],
        }
        return trans.get(self._lifted_index, "")

    @property
    def rh2m(self) -> int:
        """Return 2m Relative Humidity."""
        return self._rh2m

    @property
    def rh2m_plain(self) -> str:
        """Return 2m Relative Humidity."""
        return RH2M_PLAIN[self._rh2m - 4]

    @property
    def wind10m_direction(self) -> str:
        """Return 10m Wind Direction."""
        return self._wind10m.get("direction", "O")

    @property
    def wind10m_speed(self) -> int:
        """Return 10m Wind Speed."""
        return self._wind10m.get("speed", -1)

    @property
    def wind10m_speed_plain(self) -> str:
        """Return 10m Wind Speed."""
        return WIND10M_SPEED_PLAIN[self._wind10m.get("speed", -1) - 1]

    @property
    def temp2m(self) -> int:
        """Return 2m Temperature."""
        return self._temp2m

    @property
    def prec_type(self) -> str:
        """Return Precipitation Type."""
        return self._prec_type

    @property
    def forecast0(self) -> []:
        """Return Forecast."""
        fc = round(
            (
                self._forecast[0].get("condition", -1)
                + self._forecast[1].get("condition", -1)
                + self._forecast[2].get("condition", -1)
            )
            / 3,
            1,
        )
        return fc

    @property
    def forecast0_plain(self) -> []:
        """Return Forecast."""
        _LOGGER.debug(
            "forecast0_plain: H{}:C{}:S{}:T{}:{}-H{}:C{}:S{}:T{}:{}-H{}:C{}:S{}:T{}:{}".format(
                self._forecast[0].get("hour", -1),
                self._forecast[0].get("cloudcover", -1),
                self._forecast[0].get("seeing", -1),
                self._forecast[0].get("transparency", -1),
                CONDITION[self._forecast[0].get("condition", -1) - 1],
                self._forecast[1].get("hour", -1),
                self._forecast[1].get("cloudcover", -1),
                self._forecast[1].get("seeing", -1),
                self._forecast[1].get("transparency", -1),
                CONDITION[self._forecast[1].get("condition", -1) - 1],
                self._forecast[2].get("hour", -1),
                self._forecast[2].get("cloudcover", -1),
                self._forecast[2].get("seeing", -1),
                self._forecast[2].get("transparency", -1),
                CONDITION[self._forecast[2].get("condition", -1) - 1],
            )
        )
        return "{}-{}-{}".format(
            CONDITION[self._forecast[0].get("condition", -1) - 1],
            CONDITION[self._forecast[1].get("condition", -1) - 1],
            CONDITION[self._forecast[2].get("condition", -1) - 1],
        )

    @property
    def forecast1(self) -> []:
        """Return Forecast."""
        fc = round(
            (
                self._forecast[3].get("condition", -1)
                + self._forecast[4].get("condition", -1)
                + self._forecast[5].get("condition", -1)
            )
            / 3,
            1,
        )
        return fc

    @property
    def forecast1_plain(self) -> []:
        """Return Forecast."""
        _LOGGER.debug(
            "forecast1_plain: H{}:C{}:S{}:T{}:{}-H{}:C{}:S{}:T{}:{}-H{}:C{}:S{}:T{}:{}".format(
                self._forecast[0].get("hour", -1),
                self._forecast[3].get("cloudcover", -1),
                self._forecast[3].get("seeing", -1),
                self._forecast[3].get("transparency", -1),
                CONDITION[self._forecast[3].get("condition", -1) - 1],
                self._forecast[1].get("hour", -1),
                self._forecast[4].get("cloudcover", -1),
                self._forecast[4].get("seeing", -1),
                self._forecast[4].get("transparency", -1),
                CONDITION[self._forecast[4].get("condition", -1) - 1],
                self._forecast[2].get("hour", -1),
                self._forecast[5].get("cloudcover", -1),
                self._forecast[5].get("seeing", -1),
                self._forecast[5].get("transparency", -1),
                CONDITION[self._forecast[5].get("condition", -1) - 1],
            )
        )
        return "{}-{}-{}".format(
            CONDITION[self._forecast[3].get("condition", -1) - 1],
            CONDITION[self._forecast[4].get("condition", -1) - 1],
            CONDITION[self._forecast[5].get("condition", -1) - 1],
        )

    @property
    def deep_sky_view(self) -> bool:
        """Return True if Deep Sky should be possible."""
        if self._forecast[0].get("condition", -1) <= DEEP_SKY_THRESHOLD:
            return True

        return False

    @property
    def view_condition(self) -> int:
        """Return Current View Conditions."""
        return self._forecast[0].get("condition", -1)

    @property
    def view_condition_plain(self) -> str:
        """Return Current View Conditions."""
        return CONDITION[self._forecast[0].get("condition", -1) - 1]
