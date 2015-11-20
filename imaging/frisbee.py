import time
import re

import asyncio
import telnetlib3

from logger import logger

class FrisbeeParser(telnetlib3.TerminalShell):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.bytes_line = b""
        self.total_chunks = 0

    def feed_byte(self, x):
        if x == b"\n":
            self.parse_line()
            self.bytes_line = b""
        else:
            self.bytes_line += x

    def ip(self):
        return self.client.proxy.control_ip
    def feedback(self, field, msg):
        self.client.proxy.message_bus.put_nowait({'ip': self.ip(), field: msg})
    def send_percent(self, percent):
        self.feedback('frisbee_progress', percent)

    # parse frisbee output
    # tentatively ported from nitos_testbed ruby code but never tested
    matcher_new_style_progress = re.compile('[\.sz]{60,75}\s+\d+\s+(?P<remaining_chunks>\d+)')
    matcher_total_chunks = re.compile('.*team after (?P<time>[0-9\.]*).*File is (?P<total_chunks>[0-9]+) chunks.*')
    matcher_old_style_progress = re.compile('^Progress:\s+(?P<percent>[\d]+)%.*')
    matcher_final_report = re.compile('^Wrote\s+(?P<total>\d+)\s+bytes \((?P<actual>\d+).*')
    matcher_short_write = re.compile('.*Short write.*')
    matcher_status = re.compile('FRISBEE-STATUS=(?P<status>\d+)')

    def parse_line(self):
        line = self.bytes_line.decode().strip()
        #
        m = self.matcher_new_style_progress.match(line)
        if m:
            if self.total_chunks == 0:
                logger.error("ip={}: new frisbee: cannot report progress, missing total chunks"
                             .format(self.ip()))
                return
            percent = int ( 100 * (1 - int(m.group('remaining_chunks'))/self.total_chunks))
            self.send_percent(percent)
        #
        m = self.matcher_total_chunks.match(line)
        if m:
            self.total_chunks = int(m.group('total_chunks'))
            self.send_percent(1)
            return
        #
        m = self.matcher_old_style_progress.match(line)
        if m:
            self.send_percent(m.group('percent'))
            return
        #
        m = self.matcher_final_report.match(line)
        if m:
            logger.info("ip={ip} FRISBEE END: total = {total} bytes, actual = {actual} bytes"
                  .format(ip=self.ip(), total=m.group('total'), actual=m.group('actual')))
            self.send_percent(100)
            return
        #
        m = self.matcher_short_write.match(line)
        if m:
            self.feedback('frisbee_error', "Something went wrong with frisbee (short write...)...")
            return
        #
        m = self.matcher_status.match(line)
        if m:
            status = int(m.group('status'))
            self.feedback('frisbee_retcod', status)
            

class FrisbeeClient(telnetlib3.TelnetClient):
    def __init__(self, proxy, *args, **kwds):
        self.proxy = proxy
        super().__init__(*args, **kwds)

class FrisbeeProxy:
    """
    a convenience class that help us
    * wait for the telnet server to come up
    * invoke frisbee
    """
    def __init__(self, control_ip, message_bus, port=23, interval=1., loop=None):
        self.control_ip = control_ip
        self.message_bus = message_bus
        self.port = port
        # how often to chec kfor the connection
        self.interval = interval
        self.loop = loop if loop is not None else asyncio.get_event_loop()
        # internals
        self._transport = None
        self._protocol = None

    def is_ready(self):
        # xxx for now we don't check that frisbee is installed and the expected version
        return self._protocol is not None

    @asyncio.coroutine
    def feedback(self, field, msg):
        yield from self.message_bus.put({'ip': self.control_ip, field: msg})

    @asyncio.coroutine
    def wait(self):
        """
        wait for the telnet server to come up
        this has no native timeout mechanism
        """
        while True:
             yield from self.try_to_connect()
             if self.is_ready():
                 return True
             else:
                 yield from self.feedback(
                     'frisbee_status',
                     "backing off for {}..".format(self.control_ip, self.interval))
                 yield from asyncio.sleep(self.interval)

    @asyncio.coroutine
    def try_to_connect(self):
        
        # a little closure to capture our ip and expose it to the parser
        def client_factory():
            return FrisbeeClient(proxy = self, encoding='utf-8', shell=FrisbeeParser)

        yield from self.feedback('frisbee_status', "trying to telnet")
        try:
            self._transport, self._protocol = \
              yield from self.loop.create_connection(client_factory, self.control_ip, self.port)
            yield from self.feedback('frisbee_status', "telnet connected")
            return True
        except Exception as e:
#            import traceback
#            traceback.print_exc()
            # just making sure
            self._transport, self._protocol = None, None

    @asyncio.coroutine
    def run_client(self, multicast_ip, port):
        control_ip = self.control_ip
        from config import the_config
        client = the_config.value('frisbee', 'client')
        hdd = the_config.value('frisbee', 'hard_drive')
        self.command = \
          "{client} -i {control_ip} -m {multicast_ip} -p {port} {hdd}".format(**locals())

        yield from self.feedback('frisbee_status', "running command {}"
                                .format(self.command))
        EOF = chr(4)
        EOL = '\n'
        # print out exit status so the parser can catch it and expose it
        command = self.command
        command = command + "; echo FRISBEE-STATUS=$?"
        # make sure the command is sent (EOL) and that the session terminates afterwards (exit + EOF)
        command = command + "; exit" + EOL + EOF
        self._protocol.stream.write(self._protocol.shell.encode(command))

        # xxx should maybe handle timeout here with some kind of loop...
        # wait for telnet to terminate
        yield from self._protocol.waiter_closed