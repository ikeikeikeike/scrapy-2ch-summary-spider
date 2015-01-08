# -*- coding: utf-8 -*-
import re
import itertools

from scrapy import log
from scrapy.selector import Selector

from summaries.items import SummariesItem

from thread_float_bbs import (
    SequenceAppend,
    ThreadFloatBbsSpider
)


class AnigeSokuhouvipSpider(ThreadFloatBbsSpider):
    """ for www.anige-sokuhouvip.com
    """
    name = 'anige_sokuhouvip'
    allowed_domains = ['www.anige-sokuhouvip.com']
    start_urls = ['http://www.anige-sokuhouvip.com/?xml']

    def spider_page(self, response):
        """ scraping page
        """
        sel = Selector(response)

        image_urls = []
        contents = SequenceAppend({
            "index": int,
            "subject": '',
            "body": ''
        })

        main = sel.css('div.entry-body')
        for sub, body in itertools.izip(main.css('.t_h'), main.css('.t_b')):

            image_urls.extend(sub.css('img').xpath('@src').extract())
            image_urls.extend(body.css('img').xpath('@src').extract())

            contents.append({
                "subject": sub.extract(),
                "body": body.extract()
            })

        item = dict(
            posted=False,
            source=self.extract_source(sel),
            url=response.url,
            title=self.get_text(sel.xpath('//h2')),
            tags=self.extract_tags(main, response),
            contents=contents.result(),
            image_urls=image_urls
        )
        # set title from source.
        return self.request_title(item['source'], SummariesItem(**item))

    def extract_source(self, selector):
        """ Sourceを抽出
        """
        try:
            url = [
                text for text
                in selector.css('div').xpath('text()').extract()
                if text.find('2ch.net') != -1
                or text.find('2ch.sc') != -1
            ][0]
            return re.search("(?P<url>https?://[^\s]+)", url).group("url")
        except Exception as exc:
            log.msg(
                format=("Extract source (error): "
                        "Error selector %(selector)s "
                        "url `%(url)s`: %(errormsg)s"),
                level=log.WARNING,
                spider=self,
                selector=selector,
                url=selector.response.url,
                errormsg=str(exc))
        return None

    def extract_tags(self, selector, response):
        """ tagsを抽出
        """
        try:
            feed = self.get_feed(response.url)
            tag = self.get_text(selector.xpath('p/a')[0])

            return list({feed['tags'][0]['term'], tag})
        except Exception as exc:
            log.msg(
                format=("Extract tags (error): "
                        "Error selector %(selector)s "
                        "url `%(url)s`: %(errormsg)s"),
                level=log.WARNING,
                spider=self,
                selector=selector,
                url=response.url,
                errormsg=str(exc))
        return []
