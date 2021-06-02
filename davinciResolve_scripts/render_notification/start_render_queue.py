import sys
import os
from threading import Timer
from datetime import datetime

from slack import WebClient
from slack.errors import SlackApiError

from dotenv import load_dotenv

from python_get_resolve import GetResolve

# load .env file
load_dotenv('.env')

# init resolve API
try:
    resolve = GetResolve()
    projectManager = resolve.GetProjectManager()
except AttributeError:
    print('Unable to load module for Resolve Studio! Loading module for free version of Davinci Resolve...')
    try:
        # app is a reference to the existing Fusion application instance
        resolve = app.GetResolve()
        projectManager = resolve.GetProjectManager()
    except AttributeError:
        print('Unable to load module! Exiting...')
    sys.exit(1)

# load job queue
project = projectManager.GetCurrentProject()
render_queue_list = project.GetRenderJobList()


def run_once(f):
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)

    wrapper.has_run = False
    return wrapper


class RepeatingTimer:

    # Special thanks to alexbw for timer: https://gist.github.com/alexbw/1187132

    '''
        USAGE:
        from time import sleep

        def myFunction(inputArgument):
                print(inputArgument)

        r = RepeatingTimer(0.5, myFunction, "hello")
        r.start(); sleep(2); r.interval = 0.05; sleep(2); r.stop()
    '''

    def __init__(self, interval, function, *args, **kwargs):
        super(RepeatingTimer, self).__init__()
        self.args = args
        self.kwargs = kwargs
        self.function = function
        self.interval = interval

    def start(self):
        self.callback()

    def stop(self):
        self.interval = False

    def callback(self):
        if self.interval:
            self.function(*self.args, **self.kwargs)
            Timer(self.interval, self.callback).start()


class RenderAndSlack:
    def __init__(self):
        self._job_index = 0

        # Resolve 17 has changed job index from int(index) to str('JobIds')
        self._job_index_s = ''

        self._percent_status = 0
        self._current_percent = 0
        self._flag = False
        self._thread = None
        self.job_name = None
        self.timeline_name = None
        self.job_path = None
        self.filename_output = None

    @staticmethod
    def s_send_message(message: str):
        sc = WebClient(token=os.getenv('S_TOKEN'))
        try:
            msg = sc.chat_postMessage(
                text=message, channel=os.getenv('S_USER_ID'), as_user=True)
        except SlackApiError as e:
            print(f"Slack error: {e.response['error']}")

    @run_once
    def stuck(self):
        print(
            f'[!] Something probably stuck during "{self.filename_output}" render. Check it, please!')
        self.s_send_message(
            f'[!] Something probably stuck during "{self.filename_output}" render. Check it, please!')

    def check_percent(self):
        if self._current_percent == 0:
            pass
        elif self._percent_status != self._current_percent:
            # print(f"\n{self._percent_status} - {self._current_percent}")
            self._percent_status = self._current_percent
        else:
            # print(f"\n{self._percent_status} - {self._current_percent}")
            self.stuck()

    def run_thread(self, render_delay):
        t = RepeatingTimer(render_delay, self.check_percent)
        t.start()
        return t

    def render_now(self, index, filename):
        if project.StartRendering(index):
            print(f'[>] Start rendering "{filename}"...', end='\n')
            start = datetime.now().timestamp()

            while project.IsRenderingInProgress():
                self._current_percent = project.GetRenderJobStatus(index)[
                    'CompletionPercentage']
                if self._flag is not True:
                    if self._current_percent > 1.0:
                        stop = datetime.now().timestamp()
                        render_delay = ((stop - start) * 5)
                        self._thread = self.run_thread(render_delay)
                        print(f'[>] Percent delay: {round(render_delay, 1)}s')
                        self._flag = True
            else:
                self._thread.stop()
                if project.GetRenderJobStatus(index)['JobStatus'] == 'Complete':
                    print(f'[+] Render "{filename}" completed.\n')
                    self.s_send_message(f'File "{filename}" completed.')
                elif project.GetRenderJobStatus(index)['JobStatus'] == 'Cancelled':
                    print(f'[-] Render {filename} cancelled!\n')
        else:
            raise TypeError('Resolve function(StartRendering) returns False')

    def prepare_jobs(self, queue_jobs):
        if queue_jobs:
            while self._job_index < len(queue_jobs):
                self._percent_status = 0
                self._flag = False
                self._job_index_s = queue_jobs[self._job_index]['JobId']
                self.job_name = queue_jobs[self._job_index]['RenderJobName']
                self.timeline_name = queue_jobs[self._job_index]['TimelineName']
                self.job_path = queue_jobs[self._job_index]['TargetDir']
                self.filename_output = queue_jobs[self._job_index]['OutputFilename']

                print(f'\nProceed: {self.job_name}\n'
                      f'Timeline: {self.timeline_name}\n'
                      f'Target Dir: {self.job_path}\n'
                      f'Output filename: {self.filename_output}\n')

                self.render_now(self._job_index_s, self.filename_output)
                self._job_index += 1
        else:
            print('[!] No job(s) in queue!')


if __name__ == '__main__':
    ras = RenderAndSlack()
    ras.prepare_jobs(render_queue_list)
