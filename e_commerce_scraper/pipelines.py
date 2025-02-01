from scrapy.exporters import JsonLinesItemExporter


class JsonPipeline:
    def open_spider(self, spider):
        self.file = open('scraped_data.json', 'ab')  # Open file in binary mode for JSON lines
        self.exporter = JsonLinesItemExporter(self.file, ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item
