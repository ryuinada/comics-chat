#!/usr/local/bin/perl

$SIG{'HUP'}=$SIG{'INT'}=$SIG{'QUIT'}=$SIG{'TERM'}=$SIG{'ALRM'}='terminate';
sub terminate {
	kill -9, $$;
	exit(0);
}

alarm 600;

print "Content-type: text/html; charset=ISO-2022-JP\n\n";
print '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">',"\n";
print '<HTML lang="ja">',"\n";
print "<HEAD>\n\n";

print '<BR CLEAR><HR>';
print '<TABLE CELLPADDING="0" BGCOLOR="#FFFFE0" BORDER="2"><TR><TD>',"\n";
print "<H2>Debug Information for $0</H2>\n";

print "<B>File ARGV Information:</B><BR>\n";

print 'File name = ','<FONT COLOR="red">',$0,"</FONT><BR>\n";
print 'File argv = ','<FONT COLOR="red">',$ARGV[0],"</FONT><BR>\n";
print 'Format File name = ','<FONT COLOR="red">',$format_file,"</FONT><BR>\n";
print "<BR>\n";

print "<BR>\n";
print "<B>ENV Information:</B><BR>\n";
foreach $key (sort keys %ENV) {
    $val = $ENV{$key};
    print $key," = ",'<FONT COLOR="red">',$val,"</FONT><BR>\n";
}
print "<BR>\n";

print "<B>Format File Information:</B><BR>\n";

open (FORMAT, "$format_file");

while (<FORMAT>) {
    &jcode'convert(*_,euc);
    $val = $_;
    if ($val =~ /^#.*for.*$start/i) {last};
  }
  while (<FORMAT>) {
    &jcode'convert(*_,euc);
    $val = $_;
    if ($val =~ /^#.*for.*$end/i) {last};
    $val =~ s/([&<>'])/&$html_ent{$1};/gmo;
    if ($name{'charset'} ne 'iso-8859-1') {
        &jcode'convert(*val,$name{'charset'});
    }
    if ($val =~ /^\$/) {
      print "<FONT COLOR=green>$val</FONT><BR>\n";
    }
    else {
      print $val,"<BR>\n";
    }
}

close (FORMAT);


print "</TD></TR></TABLE>\n";




exit 0;
