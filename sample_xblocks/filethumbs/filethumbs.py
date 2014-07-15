"""An XBlock providing thumbs-up/thumbs-down voting.

This is a completely artifical test case for the filesystem field type. 

Votes are stored in a JSON object in the file system, and up/down arrow PNGs are constructed as files on-the-fly. 
"""

import json
import png

from xblock.core import XBlock
from xblock.fields import Scope, Integer, Boolean, Filesystem
from xblock.fragment import Fragment
import pkg_resources

import logging

log = logging.getLogger(__name__)

arrow = ["11011", 
         "10001", 
         "00000", 
         "11011", 
         "11011", 
         "11011", 
         "10001"]
arrow = [map(int, x) for x in arrow]

@XBlock.needs('fs')
class FileThumbsBlock(XBlock):
    """
    An XBlock with thumbs-up/thumbs-down voting.

    Vote totals are stored for all students to see.  Each student is recorded
    as has-voted or not.

    This demonstrates multiple data scopes and ajax handlers.

    """

    upvotes = 0 #Integer(help="Number of up votes", default=0, scope=Scope.user_state_summary)
    downvotes = 0 # Integer(help="Number of down votes", default=0, scope=Scope.user_state_summary)
    voted = Boolean(help="Has this student voted?", default=False, scope=Scope.user_state)
    fs = Filesystem(help="File system", scope=Scope.user_state)

    def student_view(self, context=None):  # pylint: disable=W0613
        """
        Create a fragment used to display the XBlock to a student.
        `context` is a dictionary used to configure the display (unused)

        Returns a `Fragment` object specifying the HTML, CSS, and JavaScript
        to display.
        """

        # Load the HTML fragment from within the package and fill in the template
        html_str = pkg_resources.resource_string(__name__, "static/html/thumbs.html")
        frag = Fragment(unicode(html_str).format(self=self))

        if not self.fs.exists("votes.json"):
            f = self.fs.open("votes.json", "wb")
            json.dump({'up':0, 'down':0}, f)
            f.close()

        votes = json.load(self.fs.open("votes.json"))
        self.upvotes = votes['up']
        self.downvotes = votes['down']
            
        # Load the CSS and JavaScript fragments from within the package
        css_str = pkg_resources.resource_string(__name__, "static/css/thumbs.css")
        frag.add_css(unicode(css_str))

        js_str = pkg_resources.resource_string(__name__,
                                               "static/js/src/thumbs.js")
        frag.add_javascript(unicode(js_str))

        f = self.fs.open("uparrow.png", "wb")
        png.Writer(len(arrow[0]), len(arrow), greyscale = True, bitdepth = 1).write(f, arrow)
        f.close()
        f = self.fs.open("downarrow.png", "wb")
        png.Writer(len(arrow[0]), len(arrow), greyscale = True, bitdepth = 1).write(f, arrow[::-1])
        f.close()

        frag.initialize_js('FileThumbsBlock', {'up' : self.upvotes, 
                                               'down' : self.downvotes, 
                                               'voted': self.voted, 
                                               'uparrow' : self.fs.get_url('uparrow.png'), 
                                               'downarrow' : self.fs.get_url('downarrow.png')})
        return frag

    problem_view = student_view

    @XBlock.json_handler
    def vote(self, data, suffix=''):  # pylint: disable=unused-argument
        """
        Update the vote count in response to a user action.
        """
        # Here is where we would prevent a student from voting twice, but then
        # we couldn't click more than once in the demo!
        #
        #     if self.voted:
        #         log.error("cheater!")
        #         return

        votes = json.load(self.fs.open("votes.json"))
        self.upvotes = votes['up']
        self.downvotes = votes['down']

        if data['voteType'] not in ('up', 'down'):
            log.error('error!')
            return

        if data['voteType'] == 'up':
            self.upvotes += 1
        else:
            self.downvotes += 1

        f = self.fs.open("votes.json", "wb")
        json.dump({'up':self.upvotes, 'down':self.downvotes}, f)
        f.close()

        self.voted = True

        return {'up': self.upvotes, 'down': self.downvotes}

    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("filethumbs",
             """\
                <vertical_demo>
                    <filethumbs/>
                    <filethumbs/>
                    <filethumbs/>
                </vertical_demo>
             """)
        ]