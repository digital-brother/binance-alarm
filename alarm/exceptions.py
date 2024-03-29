class BinanceAlarmError(Exception):
    pass


class NoAlarmMessageError(BinanceAlarmError):
    pass


class PreviousCallResultsNotFetchedError(BinanceAlarmError):
    pass


class NoPreviousCallError(BinanceAlarmError):
    pass


class TelegramMessageAlreadyExistsError(BinanceAlarmError):
    pass


class NoTelegramMessageError(BinanceAlarmError):
    pass


class InactivePhoneHasUnseenThresholdBreaksError(BinanceAlarmError):
    pass


class InactivePhoneError(BinanceAlarmError):
    pass
