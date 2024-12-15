from shared.data_source import DataSource


class ConfigManager():
    def __init__(
            self,
            data_sources: list[DataSource] | None = None
    ):
        if data_sources is None:
            data_sources = []
        self.__data_sources = data_sources

    def register_data_source(self, data_source: DataSource):
        self.__data_sources.append(data_source)

    def load_all(self, config: object):
        for data_source in self.__data_sources:
            data_source.load(config)
