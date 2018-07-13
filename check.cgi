#!/usr/local/bin/perl

# get jcode.pl
require 'jcode.pl';

$| = 1;

$CHAT_HOME = "/home/akiyama/public_html/collaborate";
$LOG_FILE = "$CHAT_HOME/chat.log";
$MEMBER_DIR = "$CHAT_HOME/member";
$MEMBER_FILE = "$MEMBER_DIR/members";

$TEMP_FILE = "/tmp/check.$$";

open (LOG, "$LOG_FILE.r");

$flag = 0;
while(<LOG>){
  next if /^\s*$/;
  next if /^<BR>\s*$/;
  chomp;
  if ($flag == 1) {
    $title = $_;
    last;
  }
  if (/<\/STRONG>/) {
    $flag =1;
  }
}

close (LOG);

&jcode'convert(*title,'euc');
$title =~ s/<([^>]*)>//gmoi;
&jcode'convert(*title,'sjis');

# メンバーリストの読み込み
open (MEMBERS, "$MEMBER_FILE");
while (<MEMBERS>) {
  chomp;
  ($host, $name) = split(/,/, $_);
  $myname{$host} = $name;
}
close (MEMBERS);

# 日付の設定
# 
$now = time();
($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($now);
$thisday = ("日", "月", "火", "水", "木", "金", "土")[$wday];
$year = $year + 1900;
$mmon = $mon + 1;
$date = "$year.$mmon.$mday($thisday)　";
&jcode'convert(*date, 'sjis');

$host = $ENV{'REMOTE_HOST'};
utime ($now, $now, "$MEMBER_DIR/$host") || open (TMP, ">> $MEMBER_DIR/$host");


print "Content-type: text/html\n\n";
print "<HTML>\n\n";
print "<HEAD>\n\n";
print '<META HTTP-EQUIV="Refresh" CONTENT="180">',"\n";
print '<META HTTP-EQUIV="Pragma" CONTENT="no-cache">',"\n";
print '<META HTTP-EQUIV="Cache-Control" CONTENT="no-cache">',"\n";
print '<META HTTP-EQUIV="Expires" CONTENT="0">',"\n";

print "\n\n";
print '<META HTTP-EQUIV="Content-type" CONTENT="text/html; charset=Shift_JIS">';
print "\n\n";

#$title = "Chatting Members.";
print "<TITLE>$title";
print "</TITLE>\n\n";
print "</HEAD>\n\n";
print '<BODY LINK="#191970" ALINK="#FF0000" VLINK="#808080" BGCOLOR="#EEEEEE">', "\n\n";

$str = "<FONT SIZE=1 COLOR=#CCCCCC>FUJIXEROX INTERNAL USE ONLY, 作成責任者： 秋山浩一</FONT><BR>\n";
&jcode'convert(*str,'sjis');

printf  $str;

print "<BR>\n\n";
#print "$ENV{'REMOTE_HOST'}<BR>\n\n";
#print "$ENV{'HTTP_VIA'}<BR>\n\n";

print  '<STRONG>Recent Chat log...</STRONG><A HREF="collaborate.cgi">Write !</A><HR>';
print "\n";
open (LOG, "$LOG_FILE.r");

$count = 0;
while(<LOG>){
  next if (/<HEAD>/o);
	print $_;
#	$count++;
#	last if ($count > 20);
}

close (LOG);

print "</HTML>\n\n";
