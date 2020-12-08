import requests
import asyncio
from discord.ext import commands

from college import College
from major import Major
from emojis import emojis, numeric_emojis, num_emojis
from page import Page


url = 'https://assist.org/api/institutions'
allInstitutions = requests.get(url).json()

class Admin(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def select(self, ctx, options, kind):
        """
        The function to show users the possible options and make them select their home colleges,
        target colleges, or intended majors.
        """

        # Check if there is no option.
        if not len(options):

            if kind == 'Target College':
                await ctx.channel.send(
                    f'There is no agreement of your home college and your target college.'
                )
            else:
                await ctx.channel.send(f'{kind} Not Found!')

        # If there is only one option, it is the one we are looking for.
        elif len(options) == 1:

            if "**" not in options[0].name:
                await ctx.channel.send(f'Found your {kind}, **{options[0].name}**!')
            else:
                await ctx.channel.send(f'Found your {kind}, {options[0].name}!')

            return options[0]

        else:
            title = f'Choose from these {len(options)} options for your {kind}:'

            # Tell users what options they have.
            pages = []

            msg = ''
            count = 0
            for i in range(len(options)):
                
                if count >= 5:
                    page = Page(title, msg, count=count)
                    if pages:
                        page.prev = pages[-1]
                        pages[-1].next = page
                    pages.append(page)
                    msg = ''
                    count = 0

                msg += f'`{count + 1}` {options[i].name} '

                if kind == 'Home College' or kind == 'Target College':
                    msg += f'**{options[i].code}**'
                
                msg += '\n\n'
                count += 1
            
            page = Page(title, msg, count=count)
            if pages:
                page.prev = pages[-1]
                pages[-1].next = page
            pages.append(page)


            embed = pages[0].getEmbed()

            msg = await ctx.channel.send(embed=embed)

            await self.showReactions(msg, pages[0])

            # Check function for the wait_for function later.
            def check(reaction, user):
                emoji = str(reaction.emoji)
                return (emoji in num_emojis or emoji in emojis.values()) and user == ctx.author

            # Get the message from users.
            count = 0
            curr = pages[0]

            try:

                while True:

                    reaction, user = await self.client.wait_for('reaction_add', timeout=20.0, check=check)

                    if str(reaction.emoji) in num_emojis:
                        break

                    if str(reaction.emoji) == emojis['next']:
                        curr = curr.next
                        await msg.edit(embed=curr.getEmbed())
                        await self.showReactions(msg, curr)

                    elif str(reaction.emoji) == emojis['back']:
                        curr = curr.prev
                        await msg.edit(embed=curr.getEmbed())
                        await self.showReactions(msg, curr)
                    

            except asyncio.TimeoutError:
                await ctx.channel.send(":no_entry:  **Closed due to the inaction.**")
                await msg.delete()

            else:
                await ctx.channel.send(f'Ok! You choose {options[num_emojis[reaction.emoji] - 1].name}.')
                await msg.delete()
                return options[num_emojis[reaction.emoji] - 1]

    async def showReactions(self, msg, page):
        await msg.clear_reactions()
        
        if page.hasPrev():
            await msg.add_reaction(emojis['back'])

        for emoji in list(numeric_emojis.values())[0:page.count]:
            await msg.add_reaction(emoji)

        if page.hasNext():
            await msg.add_reaction(emojis['next'])


    @commands.command()
    async def assist(self, ctx, *arg):
        """
        First, find the possible options that the user might refer to, and help them choose.
        Second, do the same thing to the possible target colleges and the possible majors.
        And send the agreement they are looking for.
        """

        # Check if arg is empty.
        if len(arg) != 3:
            await ctx.channel.send(
                'Please follow this format:\n?assist  **"Home College"**  **"Target College"**  **"Target Major"**'
            )

        home_college = arg[0]
        target_college = arg[1]
        major = arg[2]

        # Generate the home college options.
        home_options = findColleges(home_college)

        # Show them the options and make them choose.
        final_home_college = await self.select(ctx, home_options, 'Home College')
        sending_id = final_home_college.id

        # Get the sending_id of users' final home college.
        if not sending_id:
            _, sending_id = findColleges(final_home_college.name.split("**")[0][:-1])

        # Generate the target college options and the receiving_id.
        target_options = findColleges(target_college)

        # Show them the options and make them choose.
        final_target_college = await self.select(ctx, target_options, 'Target College')
        receiving_id = final_target_college.id

        # Get the receiving_id of users' final home college.
        if not receiving_id:
            _, receiving_id = findColleges(
                final_target_college.split("**")[0][:-1])

        #
        agreement = latestAgreement(sending_id, receiving_id)

        #
        if not agreement:
            await ctx.channel.send(
                f"Sorry there is no agreement between {final_home_college.name} and {final_target_college.name}"
            )
            return

        url = f"https://assist.org/api/agreements?receivingInstitutionId={receiving_id}" \
        f"&sendingInstitutionId={sending_id}&academicYearId={agreement}&categoryCode=major"
        reports = requests.get(url).json()["reports"]
        key = 0

        major_options = findMajor(major, reports)

        final_major = await self.select(ctx, major_options, 'Major')

        for major in reports:
            if major['label'] == final_major.name:
                key = major['key']

        if key:
            await ctx.channel.send(
                f"Here is your agreement:\nhttps://assist.org/transfer/report/{key}"
            )

        else:
            await ctx.channel.send("Sorry I didn't find your agreement...")

def findColleges(target):
    """
    Find the option that is exactly the same as users' targets or the options that contain users' targets.
    """

    # Check if there is not target.
    if not target:
        return [], 0

    options = []

    # Loop through allInstitution to find potential institution.
    for institution in allInstitutions:

        code = institution['code'].split()[0]
        names = institution['names']

        # Check if the users enter the code of the school first.
        if target.lower() == code.lower():
            targetCollege = College(institution['id'], names[0]['name'], code)
            return [targetCollege]

        # Loop through the names of the institution.
        for name in names:

            # Found the option that is exactly the same as the target.
            if target.lower() == name['name'].lower():
                targetCollege = College(institution['id'], name['name'], code)
                return [targetCollege]

            # Found the option that contains the target.
            if target.lower() in name['name'].lower() or target.lower() in code.lower():
                options.append(College(institution['id'], name['name'], code))

    return options


def findMajor(target, majors):
    """
    Find the option that is exactly the same as users' targets or the options that contain users' targets.
    """

    # Check if there is no target.
    if not target:
        return []

    options = []
    words = target.split()

    # Loop through allInstitution to find potential institution.
    for major in majors:

        label = major['label']

        for word in words:

            if word.lower() in label.lower():
                options.append(Major(label))
                break

    return options



def latestAgreement(sending_id, receiving_id):
    """

    """

    url = f'https://assist.org/api/institutions/{sending_id}/agreements'

    intuitions = requests.get(url).json()

    for intuition in intuitions:
        if intuition["institutionParentId"] == receiving_id:
            return max(intuition['receivingYearIds'])

    return 0



def setup(client):
    client.add_cog(Admin(client))
