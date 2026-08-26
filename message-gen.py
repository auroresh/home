import datetime
import csv


def gen_message(
    name: str, site: str | None, message_time: datetime.datetime, body: str
):
    """Generates one HTML message content for the notess page"""
    schema = f"""
    <message role="listitem">
    <message-head>
        <message-who>
        <serif class="message-name">{name}</serif>
        { 
            f'''
            <a
                class="message-site"
                href="https://{site}"
                rel="ugc nofollow noopener"
                target="_blank"
                >{site}</a
            >
            '''
            if site is not None and site != "" else ''
        }
        </message-who>
        <time class="message-time" datetime="{message_time.now(datetime.timezone.utc).isoformat()}"
        >{message_time.day} {message_time.strftime("%b").lower()} {message_time.year} ⬩ {message_time.strftime('%H')}:{message_time.strftime("%M")}</time
        >
    </message-head>
    <p class="message-body">{body}</p>
    </message>
    """

    return schema


def gen_messages(messages: list[Message]):
    """Generates and prints all the messages as an inline-string"""
    all_messages = ""
    messages.reverse()

    for message in messages:
        all_messages += (
            gen_message(
                message.name,
                message.website,
                datetime.datetime.fromtimestamp(int(message.time) / 1e3),
                message.message,
            )
            + "\n"
        )

    return all_messages


class Message:
    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)


def main():
    with open("messages.csv", mode="r") as file:
        reader = csv.DictReader(file)
        messages = [Message(row) for row in reader]

    message_content = gen_messages(messages)

    with open("notes_template.html", mode="r") as template:
        template_content = template.read()
        done_bleh = template_content.replace("&PYTHON_FILL_MESSAGES&", message_content)
        template.close()

        with open("notes.html", mode="w") as fill_file:
            fill_file.write(done_bleh)


if __name__ == "__main__":
    main()
