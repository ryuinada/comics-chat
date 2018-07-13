#!/usr/local/bin/perl

$GIF_DIR = "/open/www/htdocs/GIF";
$CHAT_HOME = "/export/home/users/akiyama/public_html/collaborate";
$BODY_FILE = "$CHAT_HOME/chat.body";
$MEMBER_DIR = "$CHAT_HOME/member";
$LOG_FILE = "$CHAT_HOME/log";

# open (LOG, ">> $LOG_FILE");

$kidou_time = time();
$timeout = 60 * 60 * 3;

select (STDOUT); $| = 1;

$client_browser = $ENV{'HTTP_USER_AGENT'};
$host = $ENV{'REMOTE_HOST'};

# if ($client_browser =~ 'MSIE') {
if (1) {
	&gif_push("$GIF_DIR/comic2.gif");
}
else {
	print "HTTP/1.0 200 OK\n";
	print "Content-type: multipart/x-mixed-replace; boundary=---NextCheck---\n";
	print "\n";
	print "---NextCheck---\n";

		print "Content-type: image/gif\n";
		print "\n";
		&gif_push("$GIF_DIR/comic2.gif");
		print "\n";
		print "---NextCheck---\n";
		sleep(10);
		$run_filesize = -s $BODY_FILE;
		# $ctime = (stat("$MEMBER_DIR/$host"))[10];

		while (1) {
			sleep (60);
			$filesize = -s $BODY_FILE;
			if ($filesize != $run_filesize) {
				#print LOG "File Size = $filesize, $run_filesize\n";
				last;
			}
#			$ctime_now = (stat("$MEMBER_DIR/$host"))[10];
#			if ($ctime != $ctime_now) {
#				last;
#			}
			$now = time();
			if ($now - $kidou_time > $timeout) {
				#print LOG "Time = $now, $kidou_time\n";
				last;
			}
		}

		print "Content-type: image/gif\n";
        	print "\n";
        	&gif_push("$GIF_DIR/pushme2.gif");
        	print "\n";
        	print "---NextCheck---\n";

sleep (120);
}
1;

sub gif_push {
	local($file) = @_;
	open (GIF, $file);
	#select (STDOUT); $| = 1;
	while (<GIF>) {
		print;
	}
	close (GIF);
}
