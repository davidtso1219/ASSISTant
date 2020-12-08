import discord

class Page():

    def __init__(self, title, msg, count, next=None, prev=None):
        self.title = title
        self.msg = msg
        self.count = count
        self.next = next
        self.prev = prev

    def getEmbed(self):

        embed = discord.Embed(
            title=self.title,
            description=self.msg,
            color=discord.Color.blue()
        )

        return embed

    def hasNext(self):
        return self.next is not None

    def hasPrev(self):
        return self.prev is not None
