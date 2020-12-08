import discord

class Page():

    def __init__(self, title, msg, count, page_num, next=None, prev=None):
        self.title = title
        self.msg = msg
        self.count = count
        self.page_num = page_num
        self.next = next
        self.prev = prev

    def getEmbed(self):

        self.embed = discord.Embed(
            title=self.title,
            description=self.msg,
            color=discord.Color.blue(),
        )

        self.embed.set_footer(text=f'page {self.page_num}')

        return self.embed

    def hasNext(self):
        return self.next is not None

    def hasPrev(self):
        return self.prev is not None
