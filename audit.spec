%{!?python_sitearch: %define python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}

Summary: User space tools for 2.6 kernel auditing
Name: audit
Version: 2.4.5
Release: 6%{?dist}
License: GPLv2+
Group: System Environment/Daemons
URL: http://people.redhat.com/sgrubb/audit/
Source0: http://people.redhat.com/sgrubb/audit/%{name}-%{version}.tar.gz
# Remove unsupported options
Patch1: audit-2.4.5-man-page-cleanup.patch
Patch2: audit-2.4.5_escape_bug.patch
Patch3: audit-2.4.5-nispom.patch
# For bz 1369249 - Backport incremental_async flushing mode
Patch4: audit-2.4.5-incremental-async.patch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: swig python-devel openldap-devel
BuildRequires: tcp_wrappers-devel libcap-ng-devel 
BuildRequires: kernel-headers >= 2.6.29
# For autoreconf below
BuildRequires: autoconf automake libtool
Requires: %{name}-libs = %{version}-%{release}
Requires: chkconfig
Requires(pre): coreutils

%description
The audit package contains the user space utilities for
storing and searching the audit records generate by
the audit subsystem in the Linux 2.6 kernel.

%package libs
Summary: Dynamic library for libaudit
License: LGPLv2+
Group: Development/Libraries

%description libs
The audit-libs package contains the dynamic libraries needed for 
applications to use the audit framework.

%package libs-devel
Summary: Header files for libaudit
License: LGPLv2+
Group: Development/Libraries
Requires: %{name}-libs = %{version}
Requires: kernel-headers >= 2.6.29

%description libs-devel
The audit-libs-devel package contains the header files needed for
developing applications that need to use the audit framework libraries.

%package libs-static
Summary: Static version of libaudit library
License: LGPLv2+
Group: Development/Libraries
Requires: kernel-headers >= 2.6.29

%description libs-static
The audit-libs-static package contains the static libraries
needed for developing applications that need to use static audit
framework libraries

%package libs-python
Summary: Python bindings for libaudit
License: LGPLv2+
Group: Development/Libraries
Requires: %{name}-libs = %{version}-%{release}

%description libs-python
The audit-libs-python package contains the bindings so that libaudit
and libauparse can be used by python.

%package -n audispd-plugins
Summary: Plugins for the audit event dispatcher
License: GPLv2+
Group: System Environment/Daemons
BuildRequires: openldap-devel
Requires: %{name} = %{version}-%{release}
Requires: %{name}-libs = %{version}-%{release}
Requires: openldap

%description -n audispd-plugins
The audispd-plugins package provides plugins for the real-time
interface to the audit system, audispd. These plugins can do things
like relay events to remote machines or analyze events for suspicious
behavior.

%prep
%setup -q
%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1
# Remove --login-immutable
sed '/loginuid immutable/,+3d' -i contrib/nispom.rules
sed '/loginuid-immutable/,+3d' -i docs/auditctl.8
sed '/loginuid immutable/,+3d' -i contrib/stig.rules

%build
%configure --sbindir=/sbin --libdir=/%{_lib} --with-python=yes --with-python3=no --with-golang=no --with-libwrap --enable-gssapi-krb5=no --with-libcap-ng=yes --enable-zos-remote
make CFLAGS="%{optflags}" %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/{sbin,etc/{sysconfig,audispd/plugins.d,rc.d/init.d}}
mkdir -p $RPM_BUILD_ROOT/%{_mandir}/{man5,man8}
mkdir -p $RPM_BUILD_ROOT/%{_lib}
mkdir -p $RPM_BUILD_ROOT/%{_libdir}/audit
mkdir -p $RPM_BUILD_ROOT/%{_var}/log/audit
mkdir -p $RPM_BUILD_ROOT/%{_var}/spool/audit
make DESTDIR=$RPM_BUILD_ROOT install

mkdir -p $RPM_BUILD_ROOT/%{_libdir}
# This winds up in the wrong place when libtool is involved
mv $RPM_BUILD_ROOT/%{_lib}/libaudit.a $RPM_BUILD_ROOT%{_libdir}
mv $RPM_BUILD_ROOT/%{_lib}/libauparse.a $RPM_BUILD_ROOT%{_libdir}
curdir=`pwd`
cd $RPM_BUILD_ROOT/%{_libdir}
LIBNAME=`basename \`ls $RPM_BUILD_ROOT/%{_lib}/libaudit.so.1.*.*\``
ln -s ../../%{_lib}/$LIBNAME libaudit.so
LIBNAME=`basename \`ls $RPM_BUILD_ROOT/%{_lib}/libauparse.so.0.*.*\``
ln -s ../../%{_lib}/$LIBNAME libauparse.so
cd $curdir
# Remove these items so they don't get picked up.
rm -f $RPM_BUILD_ROOT/%{_lib}/libaudit.so
rm -f $RPM_BUILD_ROOT/%{_lib}/libauparse.so
rm -f $RPM_BUILD_ROOT/%{_lib}/libaudit.la
rm -f $RPM_BUILD_ROOT/%{_lib}/libauparse.la
rm -f $RPM_BUILD_ROOT/%{_libdir}/python?.?/site-packages/_audit.a
rm -f $RPM_BUILD_ROOT/%{_libdir}/python?.?/site-packages/_audit.la
rm -f $RPM_BUILD_ROOT/%{_libdir}/python?.?/site-packages/_auparse.a
rm -f $RPM_BUILD_ROOT/%{_libdir}/python?.?/site-packages/_auparse.la
rm -f $RPM_BUILD_ROOT/%{_libdir}/python?.?/site-packages/auparse.a
rm -f $RPM_BUILD_ROOT/%{_libdir}/python?.?/site-packages/auparse.la

# Move the pkgconfig file
mv $RPM_BUILD_ROOT/%{_lib}/pkgconfig $RPM_BUILD_ROOT%{_libdir}

# On platforms with 32 & 64 bit libs, we need to coordinate the timestamp
touch -r ./audit.spec $RPM_BUILD_ROOT/etc/libaudit.conf
touch -r ./audit.spec $RPM_BUILD_ROOT/usr/share/man/man5/libaudit.conf.5.gz

%ifnarch ppc ppc64
%check
make check
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%post libs -p /sbin/ldconfig

%post
# Copy default rules into place on new installation
if [ ! -e /etc/audit/audit.rules ] ; then
    cp /etc/audit/rules.d/audit.rules /etc/audit/audit.rules
fi
/sbin/chkconfig --add auditd

%preun
if [ $1 -eq 0 ]; then
   /sbin/service auditd stop > /dev/null 2>&1
   /sbin/chkconfig --del auditd
fi

%postun libs -p /sbin/ldconfig

%postun
if [ $1 -ge 1 ]; then
   /sbin/service auditd condrestart > /dev/null 2>&1 || :
fi

%files libs
%defattr(-,root,root,-)
%attr(755,root,root) /%{_lib}/libaudit.so.1*
%attr(755,root,root) /%{_lib}/libauparse.*
%config(noreplace) %attr(640,root,root) /etc/libaudit.conf
%{_mandir}/man5/libaudit.conf.5.gz

%files libs-devel
%defattr(-,root,root,-)
%doc contrib/skeleton.c contrib/plugin
%{_libdir}/libaudit.so
%{_libdir}/libauparse.so
%{_includedir}/libaudit.h
%{_includedir}/auparse.h
%{_includedir}/auparse-defs.h
%{_datadir}/aclocal/audit.m4
%{_libdir}/pkgconfig/audit.pc
%{_libdir}/pkgconfig/auparse.pc
%{_mandir}/man3/*

%files libs-static
%defattr(-,root,root,-)
%{_libdir}/libaudit.a
%{_libdir}/libauparse.a

%files libs-python
%defattr(-,root,root,-)
%attr(755,root,root) %{python_sitearch}/_audit.so
%attr(755,root,root) %{python_sitearch}/auparse.so
%{python_sitearch}/audit.py*

%files
%defattr(-,root,root,-)
%doc  README COPYING ChangeLog contrib/capp.rules contrib/nispom.rules contrib/lspp.rules contrib/stig.rules init.d/auditd.cron
%attr(644,root,root) %{_mandir}/man8/audispd.8.gz
%attr(644,root,root) %{_mandir}/man8/auditctl.8.gz
%attr(644,root,root) %{_mandir}/man8/auditd.8.gz
%attr(644,root,root) %{_mandir}/man8/aureport.8.gz
%attr(644,root,root) %{_mandir}/man8/ausearch.8.gz
%attr(644,root,root) %{_mandir}/man8/autrace.8.gz
%attr(644,root,root) %{_mandir}/man8/aulast.8.gz
%attr(644,root,root) %{_mandir}/man8/aulastlog.8.gz
%attr(644,root,root) %{_mandir}/man8/auvirt.8.gz
%attr(644,root,root) %{_mandir}/man8/augenrules.8.gz
%attr(644,root,root) %{_mandir}/man8/ausyscall.8.gz
%attr(644,root,root) %{_mandir}/man7/audit.rules.7.gz
%attr(644,root,root) %{_mandir}/man5/auditd.conf.5.gz
%attr(644,root,root) %{_mandir}/man5/audispd.conf.5.gz
%attr(644,root,root) %{_mandir}/man5/ausearch-expression.5.gz
%attr(750,root,root) /sbin/auditctl
%attr(750,root,root) /sbin/auditd
%attr(755,root,root) /sbin/ausearch
%attr(755,root,root) /sbin/aureport
%attr(750,root,root) /sbin/autrace
%attr(750,root,root) /sbin/audispd
%attr(750,root,root) /sbin/augenrules
%attr(755,root,root) %{_bindir}/aulast
%attr(755,root,root) %{_bindir}/aulastlog
%attr(755,root,root) %{_bindir}/ausyscall
%attr(755,root,root) %{_bindir}/auvirt
%attr(755,root,root) /etc/rc.d/init.d/auditd
%attr(750,root,root) %dir %{_var}/log/audit
%attr(750,root,root) %dir /etc/audit
%attr(750,root,root) %dir /etc/audit/rules.d
%attr(750,root,root) %dir /etc/audisp
%attr(750,root,root) %dir /etc/audisp/plugins.d
%attr(750,root,root) %dir %{_libdir}/audit
%config(noreplace) %attr(640,root,root) /etc/audit/auditd.conf
%config(noreplace) %attr(640,root,root) /etc/audit/rules.d/audit.rules
%ghost %config(noreplace) %attr(640,root,root) /etc/audit/audit.rules
%config(noreplace) %attr(640,root,root) /etc/sysconfig/auditd
%config(noreplace) %attr(640,root,root) /etc/audisp/audispd.conf
%config(noreplace) %attr(640,root,root) /etc/audisp/plugins.d/af_unix.conf
%config(noreplace) %attr(640,root,root) /etc/audisp/plugins.d/syslog.conf

%files -n audispd-plugins
%defattr(-,root,root,-)
%attr(644,root,root) %{_mandir}/man8/audispd-zos-remote.8.gz
%attr(644,root,root) %{_mandir}/man5/zos-remote.conf.5.gz
%config(noreplace) %attr(640,root,root) /etc/audisp/plugins.d/audispd-zos-remote.conf
%config(noreplace) %attr(640,root,root) /etc/audisp/zos-remote.conf
%attr(750,root,root) /sbin/audispd-zos-remote
%config(noreplace) %attr(640,root,root) /etc/audisp/audisp-remote.conf
%config(noreplace) %attr(640,root,root) /etc/audisp/plugins.d/au-remote.conf
%attr(750,root,root) /sbin/audisp-remote
%attr(700,root,root) %dir %{_var}/spool/audit
%attr(644,root,root) %{_mandir}/man5/audisp-remote.conf.5.gz
%attr(644,root,root) %{_mandir}/man8/audisp-remote.8.gz

%changelog
* Thu Dec 22 2016 Steve Grubb <sgrubb@redhat.com> 2.4.5-6
resolves: #1404093 - STIG rules not functional 

* Wed Sep 07 2016 Steve Grubb <sgrubb@redhat.com> 2.4.5-5
resolves: #1369249 - Backport incremental_async flushing mode

* Fri Mar 04 2016 Steve Grubb <sgrubb@redhat.com> 2.4.5-3
resolves: #1300383 - Remove --loginuid-immutable in nispom.rules file

* Wed Jan 20 2016 Steve Grubb <sgrubb@redhat.com> 2.4.5-2
resolves: #1300383 - Typo in nispom.rules file in audit package

* Fri Dec 18 2015 Steve Grubb <sgrubb@redhat.com> 2.4.5-1
- New upstream enhancement and bugfix release
resolves: #1129076 - auvirt --help shows an incorrect option "--show--uuid"
resolves: #1138674 - auditd may fail to start if configured to send mail
resolves: #1144252 - Auditctl should not send warnings to console during boot
resolves: #1197235 - ausearch can't parse time in non-US locale/UTF-8 encoding
resolves: #1235457 - Line buffer is too short for plugin config files
resolves: #1257650 - Rebase audit package

* Sun Aug 10 2014 Steve Grubb <sgrubb@redhat.com> 2.3.7-5
resolves: #1120286 - ajusted patch doing MCS translations

* Mon Jul 28 2014 Steve Grubb <sgrubb@redhat.com> 2.3.7-4
resolves: #1049916 - Handle i386 session ID's better
resolves: #1120286 - ausearch -i does not display commas between categories

* Wed Jul 02 2014 Steve Grubb <sgrubb@redhat.com> 2.3.7-3
resolves: #1111448 - Segmentation fault while run auvirt --all-events sometimes

* Mon Jun 09 2014 Steve Grubb <sgrubb@redhat.com> 2.3.7-2
Ghost audit.rules file
resolves: #967238 - Audit rules are built from a directory of rule files

* Tue Jun 03 2014 Steve Grubb <sgrubb@redhat.com> 2.3.7-1
- New upstream enhancement and bugfix release
resolves: #1065067 - Audit package rebase
resolves: #810749 - audit allows tcp_max_per_addr + 1 connections
resolves: #869555 - ausearch -i does not interpret execve arguments always
resolves: #888348 - auditd won't start when some actions send mail
resolves: #922508 - confusing aulast records for bad logins
resolves: #950158 - man page unclear wrt num_logs affecting keep_logs setting
resolves: #967238 - Audit rules are built from a directory of rule files
resolves: #967240 - ausearch to checkpoint so only reports new events
resolves: #970675 - auparse is truncating path context after first category
resolves: #1011052 - Missing text in auditd.conf man page
resolves: #1022035 - Case values for actions unclear in auditd.conf man page
resolves: #1029981 - ausearch help typo for "-x" option
resolves: #1049916 - ausearch issues found by ausearch-test
resolves: #1053424 - Error in auparse-defs.h
resolves: #1071580 - audispd config file parser fails on long input
resolves: #1089713 - limit of 30 for system call in audit.rules

* Mon Jan 27 2014 Steve Grubb <sgrubb@redhat.com> 2.2-4
- Revised patch based on upstream commit 895
resolves: #1028635 audisp-remote reconnect problems after transient network err
 
* Thu Dec 12 2013 Steve Grubb <sgrubb@redhat.com> 2.2-3
resolves: #1028635 audisp-remote reconnect problems after transient network err
 
* Tue Mar 13 2012 Steve Grubb <sgrubb@redhat.com> 2.2-2
resolves: #803349 allocate extra space for node names
 
* Fri Mar 02 2012 Steve Grubb <sgrubb@redhat.com> 2.2-1
resolves: #658630 include "check but load" option for audit
resolves: #766920 audit filtering on file accesses not owned by user
resolves: #797848 audit.rules contains a typo error

* Mon Nov 07 2011 Steve Grubb <sgrubb@redhat.com> 2.1.3-3
resolves: #715279 Auditd syslogs a message even when configured not to

* Wed Oct 26 2011 Steve Grubb <sgrubb@redhat.com> 2.1.3-2
resolves: #715279 Auditd syslogs a message even when configured not to
resolves: #748124 Auditctl doesn't recognize accept4 syscall

* Mon Aug 15 2011 Steve Grubb <sgrubb@redhat.com> 2.1.3-1
resolves: #709345 auditctl -l returns 0 even if it fails on dropped capabilities
resolves: #715279 Auditd syslogs a message even when configured not to
resolves: #715315 remote client gets disk_error event instead of disk_full
resolves: #728475 remove krb5 related options from audisp-remote.conf

* Wed Apr 27 2011 Steve Grubb <sgrubb@redhat.com> 2.1-5
resolves: #700098 - aureport --tty segfaults

* Wed Apr 20 2011 Steve Grubb <sgrubb@redhat.com> 2.1-4
resolves: #584981 - Improvements needed for Common Criteria
resolves: #697463 - Broken autrace -r on s390x

* Wed Apr 13 2011 Steve Grubb <sgrubb@redhat.com> 2.1-3
resolves: #695605 - audisp-remote calls bind() incorrectly

* Mon Apr 11 2011 Steve Grubb <sgrubb@redhat.com> 2.1-2
resolves: #584981 - Improvements needed for Common Criteria

* Wed Mar 30 2011 Steve Grubb <sgrubb@redhat.com> 2.1-1
resolves: #688664 - Logging does not resume from SYSLOG on full disk action
resolves: #647128 - audit_encode_nv_string() will crash on NULL pointer on OOM
resolves: #584981 - ausearch/report performance improvement needed

* Fri Feb 04 2011 Steve Grubb <sgrubb@redhat.com> 2.0.6-1
resolves: #584981 - ausearch/report performance improvement needed
resolves: #640948 - inodes display incorrectly when listing rules
resolves: #647128 - audit_encode_nv_string() will crash on NULL pointer on OOM
resolves: #647131 - Man page for audit_encode_nv_string() is incorrect
resolves: #670938 - searching on auid = -1 results in all events

* Wed Jan 13 2010 Steve Grubb <sgrubb@redhat.com> 2.0.4-2
- Separate out static libraries

* Wed Jan 13 2010 Steve Grubb <sgrubb@redhat.com> 2.0.4-1
- New upstream release

* Sat Oct 17 2009 Steve Grubb <sgrubb@redhat.com> 2.0.3-1
- New upstream release

* Fri Oct 16 2009 Steve Grubb <sgrubb@redhat.com> 2.0.2-1
- New upstream release

* Mon Sep 28 2009 Steve Grubb <sgrubb@redhat.com> 2.0.1-1
- New upstream release

* Fri Aug 21 2009 Steve Grubb <sgrubb@redhat.com> 2.0-3
- New upstream release
