import os
import discord
from discord.ext import commands
import requests

client = commands.Bot(command_prefix='?')

url = 'https://assist.org/api/institutions'
allInstitutions = requests.get(url).json()


# Event handlers
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')


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
            sendingID = institution['id']
            return [names[0]['name']], sendingID

        # Loop through the names of the institution.
        for name in names:

            # Found the option that is exactly the same as the target.
            if target.lower() == name['name'].lower():
                sendingID = institution['id']
                return [name['name']], sendingID

            # Found the option that contains the target.
            if target.lower() in name['name'].lower() or target.lower() in code.lower():
                options.append(name['name'] + f' **{code}**')

    return options, 0


def findMajor(target, url):
    """
    Find the option that is exactly the same as users' targets or the options that contain users' targets.
    """

    # Check if there is no target.
    if not target:
        return []

    options = []
    majors = requests.get(url).json()["reports"]
    words = target.split()

    # Loop through allInstitution to find potential institution.
    for major in majors:

        label = major['label']

        for word in words:

            if word.lower() in label.lower():
                options.append(label)
                break

    return options


async def select(ctx, options, kind):
    """
    The function to show users the possible options and make them select their home colleges,
    target colleges, or intended majors.
    """

    # Check if there is no option.
    if not len(options):

        if kind == 'Home College':
            await ctx.channel.send(f'Home College Not Found!')

        elif kind == 'Target College':
            await ctx.channel.send(
                f'There is no agreement of your home college and your target college.'
            )

    # If there is only one option, it is the one we are looking for.
    elif len(options) == 1:

        if "**" not in options[0]:
            await ctx.channel.send(f'Found your {kind}, **{options[0]}**!')
        else:
            await ctx.channel.send(f'Found your {kind}, {options[0]}!')

        return options[0]

    else:
        title = f'Choose from these {len(options)} options for your {kind}:'

        # Tell users what options they have.
        msg = ''
        for i in range(len(options)):
            msg += f'`({i + 1})` `{options[i]}`\n'

        embed = discord.Embed(
            title=title,
            description=msg,
            color=discord.Color.blue()
        )

        await ctx.channel.send(embed=embed)

        # Check function for the wait_for function later.
        def check(m):
            try:
                num = int(m.content)
                return m.channel == ctx.channel and 1 <= num <= len(
                    options) and m.author == ctx.author
            except ValueError:
                return False

        # Get the message from users.
        msg = await client.wait_for('message', check=check)
        await ctx.channel.send(
            f'Ok! You choose {options[int(msg.content) - 1]}.')
        return options[int(msg.content) - 1]


def latestAgreement(sending_id, receiving_id):
    """

    """

    url = f'https://assist.org/api/institutions/{sending_id}/agreements'

    intuitions = requests.get(url).json()

    for intuition in intuitions:
        if intuition["institutionParentId"] == receiving_id:
            return max(intuition['receivingYearIds'])

    return 0


@client.command()
async def assist(ctx, *arg):
    """
    First, find the possible options that the user might refer to, and help them choose.
    Second, do the same thing to the possible target colleges and the possible majors.
    And send the agreement they are looking for.
    """

    # Check if arg is empty.
    if not len(arg):
        await ctx.channel.send(
            'Please follow this format:\n?assist  **"Home College"**  **"Target College"**  **"Target Major"**'
        )

    home_college = arg[0]
    target_college = arg[1]
    major = arg[2]

    # Generate the home college options and the sending_id.
    home_options, sending_id = findColleges(home_college)

    # Show them the options and make them choose.
    final_home_college = await select(ctx, home_options, 'Home College')

    # Get the sending_id of users' final home college.
    if not sending_id:
        _, sending_id = findColleges(final_home_college.split("**")[0][:-1])

    # Generate the target college options and the receiving_id.
    target_options, receiving_id = findColleges(target_college)

    # Show them the options and make them choose.
    final_target_college = await select(ctx, target_options, 'Target College')

    # Get the receiving_id of users' final home college.
    if not receiving_id:
        _, receiving_id = findColleges(
            final_target_college.split("**")[0][:-1])

    #
    agreement = latestAgreement(sending_id, receiving_id)

    #
    if not agreement:
        await ctx.channel.send(
            f"Sorry there is no agreement between {final_home_college} and {final_target_college}"
        )
        return

    url = f"https://assist.org/api/agreements?receivingInstitutionId={receiving_id}" \
       f"&sendingInstitutionId={sending_id}&academicYearId={agreement}&categoryCode=major"
    reports = requests.get(url).json()["reports"]
    key = 0

    major_options = findMajor(major, url)

    final_major = await select(ctx, major_options, 'Major')

    for major in reports:
        if major['label'] == final_major:
            key = major['key']

    if key:
        await ctx.channel.send(
            f"Here is your agreement:\nhttps://assist.org/transfer/report/{key}"
        )

    else:
        await ctx.channel.send("Sorry I didn't find your agreement...")


client.load_extension('server')
client.run(os.environ['TOKEN'])