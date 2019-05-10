# Define global settings
%global _hardened_build 1
%global major_version 3
%global minor_version 5
%global micro_version 6

Name:		charybdis
Version:	%{major_version}.%{minor_version}.%{micro_version}
Release:	1%{?dist}
Summary:	A highly-scalable IRCv3-compliant IRC daemon

Group:		Applications/Communications
License:	GPLv2
URL:		https://charybdis-ircd.github.io/
Source0:	https://github.com/%{name}-ircd/%{name}/archive/%{name}-%{version}.tar.gz
Source1:	%{name}.service
Source2:	%{name}.tmpfiles
Source3:	%{name}.conf
Source4:	%{name}.README

Patch1:		%{name}-%{version}-werror.patch
Patch2:		%{name}-%{version}-ratbox.patch

Provides:	%{name} = %{version}-%{release}

BuildRequires:	bison
BuildRequires:	flex
BuildRequires:	gcc
BuildRequires:	gcc-c++
BuildRequires:	libtool
BuildRequires:	pkgconfig(sqlite3)
BuildRequires:	pkgconfig(zlib)
BuildRequires:	pkgconfig(libcrypto)

BuildRequires:		systemd
Requires(post):		systemd
Requires(preun):	systemd
Requires(postun):	systemd
Requires(pre):		shadow-utils

Requires:	openssl

%description
Charybdis is an IRCv3 server designed to be highly scalable. It implements IRCv3.1 and some parts of IRCv3.2.

It is meant to be used with an IRCv3-capable services implementation such as Atheme or Anope.

Charybdis is an ircd used on various networks either as itself, or as the basis of a customized IRC server implementation. A derivative of charybdis, ircd-seven powers freenode, which is the largest IRC network in the world.

%prep
%setup -q -n %{name}-%{name}-%{version}
%patch -P 1 -P 2 -p1

%build
%configure --enable-fhs-paths \
	--prefix=%{_prefix} \
	--with-rundir=/run \
	--sysconfdir=%{_sysconfdir}/%{name} \
	--with-moduledir=%{_libdir}/%{name} \
	--with-logdir=%{_var}/log/%{name} \
	--localstatedir=%{_sharedstatedir} \
	--libexecdir=%{_libexecdir} \
	--enable-openssl \
	--enable-ipv6 \
	--with-program-prefix=charybdis- \
	--enable-epoll

make %{?_smp_mflags} CHARYBDIS_VERSION="%{version}"

# Extra readme
cp %{SOURCE4} %{_builddir}/%{name}-%{name}-%{version}/README.info

%install
rm -rf $RPM_BUILD_ROOT
%make_install

# Move the binaries to the libexec directory, since it's
# more appropriate. This could change in the future.
%{__install} -d -m 0755 ${RPM_BUILD_ROOT}/%{_libexecdir}/%{name}
%{__mv} ${RPM_BUILD_ROOT}/%{_bindir}/* \
	${RPM_BUILD_ROOT}/%{_libexecdir}/%{name}

# Install service
%{__install} -d -m 0755 ${RPM_BUILD_ROOT}%{_unitdir}
%{__install} -m 0644 %{SOURCE1} \
        ${RPM_BUILD_ROOT}%{_unitdir}/%{name}.service

# Install tmpfiles
%{__install} -d -m 0755 ${RPM_BUILD_ROOT}%{_tmpfilesdir}
%{__install} -m 0644 %{SOURCE2} \
	${RPM_BUILD_ROOT}%{_tmpfilesdir}/%{name}.conf

# Install ircd.conf
%{__install} -m 0660 %{SOURCE3} \
	${RPM_BUILD_ROOT}/%{_sysconfdir}/%{name}/ircd.conf

# Removing development libraries
rm -rf ${RPM_BUILD_ROOT}%{_libdir}/pkgconfig
rm     ${RPM_BUILD_ROOT}%{_libdir}/libratbox.la

%pre
%{_sbindir}/groupadd -r %{name} 2>/dev/null || :
%{_sbindir}/useradd -r -g %{name} \
	-s /sbin/nologin -d %{_datadir}/%{name} \
	-c 'Charybdis Server' %{name} 2>/dev/null || :

%preun
%if 0%{?fedora} || 0%{?rhel} >= 7
%systemd_preun %{name}.service
%endif

%post
%if 0%{?fedora} || 0%{?rhel} >= 7
%systemd_post %{name}.service
systemd-tmpfiles --create %{name}.conf || :
%endif

%postun
%if 0%{?fedora} || 0%{?rhel} >= 7
%systemd_postun_with_restart %{name}.service
%endif


%files
%defattr(-, root, root, -)
%doc doc/Ratbox-team doc/Tao-of-IRC.940110 doc/operguide.txt doc/opermyth.txt doc/README.cidr_bans doc/services.txt doc/extban.txt doc/extended-join.txt doc/hooks.txt doc/CIDR.txt doc/Hybrid-team doc/modes.txt doc/monitor.txt README.md NEWS.md LICENSE CREDITS README.info
%dir %attr(0750,charybdis,charybdis) %{_var}/log/%{name}
%dir %attr(0750,charybdis,charybdis) %{_sharedstatedir}/%{name}
%dir %attr(0750,root,charybdis) %{_sysconfdir}/%{name}
%dir %{_libexecdir}/%{name}
%dir %{_libdir}/%{name}
%dir %{_libdir}/%{name}/autoload
%dir %{_libdir}/%{name}/extensions
%dir %{_datadir}/%{name}
%dir %{_datadir}/%{name}/help
%dir %{_datadir}/%{name}/help/opers
%dir %{_datadir}/%{name}/help/users
%{_libdir}/*.so
%{_libdir}/%{name}/*.so
%{_libdir}/%{name}/autoload/*.so
%{_libdir}/%{name}/extensions/*.so
%{_datadir}/%{name}/help/opers/*
%{_datadir}/%{name}/help/users/*
%{_unitdir}/%{name}.service

%attr(0755,charybdis,charybdis) %{_libexecdir}/%{name}/*

# Default configuration
%config(noreplace) %attr(0640,charybdis,charybdis) %{_sysconfdir}/%{name}/ircd.conf
%config(noreplace) %attr(0640,charybdis,charybdis) %{_sysconfdir}/%{name}/ircd.motd

%attr(0640,charybdis,charybdis) %{_sysconfdir}/%{name}/*.example
%attr(0640,charybdis,charybdis) %{_sysconfdir}/%{name}/reference.conf

%{_mandir}/man8/charybdis-ircd.8*
%{_tmpfilesdir}/%{name}.conf

# Excludes - commented since we're using rm instead at build
#%exclude %{_libdir}/*.la
#%exclude %dir %{_libdir}/pkgconfig
#%exclude %{_libdir}/pkgconfig/libratbox.pc

%changelog
* Fri May 10 2019 Louis Abel <tucklesepk@gmail.com> - 3.5.6-1
- Initial build of charybdis
- Patch WError that caused compilation to fail
- Patch the libratbox file to ensure no conflict with ircd-ratbox

