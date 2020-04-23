import bs4
import requests
import os
import threading

from urllib.parse import urljoin


class PageNode:

    def __init__(self, response):
        """Constructs a PageNode from a webpage which is a structural node in the "crawl-graph" produced by Spider

        :param response: the HTTP response when GET request made to page
        """
        self.page = response
        self.children = {}
        self.children_lock = threading.Lock()

    def get_urls(self):
        # Return all hrefs from the page
        soup = bs4.BeautifulSoup(self.page.text, 'html.parser')
        urls = []
        for a in soup.select('a'):
            urls.append(urljoin(self.page.url, a.get('href')))
        return urls

    def add_child(self, child):
        """Adds a child node to this node

        :param child: the child's PageNode
        :returns: None
        """
        self.children_lock.acquire()
        self.children[child.page.url] = child
        self.children_lock.release()

    def __str__(self):
        return self.page.url


class Spider:

    def __init__(self, root):
        self.discovered_urls = {}
        self.next_urls = {root: None}
        self.discovered_lock = threading.Lock()

    def _process_url(self, url, parent):
        """Retrieves the page at a url and parses it, adding an index entry to Spider and updating all state

        :param url: the page url to process
        :param parent: the parent's PageNode
        :returns: None
        """
        try:
            response = requests.get(url)
        except Exception:
            return
        page_node = PageNode(response)
        if parent:
            parent.add_child(page_node)
        embedded_urls = page_node.get_urls()
        for url in embedded_urls:
            if url not in self.discovered_urls:
                self.discovered_urls[url] = page_node
                self.next_urls[url] = page_node

    def crawl(self):
        """Crawls one level deeper through hyperlinks

        :returns: number of links to crawl *next* iteration
        """
        # Iterate through the next_urls at this iteration and initalize object with a fresh set
        next_urls = self.next_urls
        self.next_urls = {}
        threads = []
        for url, parent in next_urls.items():
            t = threading.Thread(target=self._process_url, args=(url, parent,))
            threads.append(t)
        [t.start() for t in threads]
        [t.join() for t in threads]
        return len(self.next_urls)


def main():
    if len(os.sys.argv) < 3:
        print('Give the search depth and starting url as command line arguments')

    depth = int(os.sys.argv[1])
    root_url = os.sys.argv[2]
    spider = Spider(root_url)
    for _ in range(depth):
        num_urls = spider.crawl()
        print(f'{num_urls} urls to search next iteration')


if __name__ == "__main__":
    main()