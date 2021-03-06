import abc

DEFAULT_HOST = 'e'
DEFAULT_PORT = 1025

class AbstractNotifications(abc.ABC):
    @abc.abstractmethod
    def send(self, destination, message):
        raise NotImplementedError


class EmailNotification(AbstractNotifications):
    #def __init__(self):
        # self.server = smtplib.SMTP(smtp_host, port=port)
        # self.server.noop()

    def send(self, destination, message):
        msg = f'Subject: allocation service notification\n{message}'
        # self.server.sendmail(from_addr='allocations@example.com', to_addrs=[destination], msg=msg)
        print(msg)
