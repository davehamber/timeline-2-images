"""ASCII art banner for timeline-2-images application."""

# ruff: noqa: E501
# pylint: disable=line-too-long


def _pad_version(version: str, width: int = 10) -> str:
    """Pad version string to width with right-aligned spaces."""
    return version.ljust(width)


class BannerPrinter:
    """Displays ASCII art banner with lilac and deep purple colors."""

    LILAC = "\033[38;2;200;162;200m"
    DEEP_PURPLE = "\033[38;2;138;43;226m"
    WHITE = "\033[38;2;255;255;255m"
    DARK_GREY = "\033[38;2;100;100;100m"
    RESET = "\033[0m"

    @classmethod
    def print_banner(cls) -> None:
        """Display ASCII art banner with lilac and deep purple colors."""
        from timeline_2_images import __version__

        dp = cls.DEEP_PURPLE
        lilac = cls.LILAC
        white = cls.WHITE
        dg = cls.DARK_GREY
        reset = cls.RESET

        banner = f"""
{dp}╔═════════════════════════════════════════════════════════════════╗{reset}
{dp}║{reset}                                                                 {dp}║{reset}
{dp}║{reset}  {lilac}████████{reset}{dp}╗{reset}{lilac}██{reset}{dp}╗{reset}{lilac}███{reset}{dp}╗{reset}   {lilac}███{reset}{dp}╗{reset}{lilac}███████{reset}{dp}╗{reset}{lilac}██{reset}{dp}╗{reset}     {lilac}██{reset}{dp}╗{reset}{lilac}███{reset}{dp}╗{reset}   {lilac}██{reset}{dp}╗{reset}{lilac}███████{reset}{dp}╗{reset}   {dp}║{reset}
{dp}║{reset}  {dp}╚══{lilac}██{reset}{dp}╔══╝{reset}{lilac}██{reset}{dp}║{reset}{lilac}████{reset}{dp}╗{reset} {lilac}████{reset}{dp}║{reset}{lilac}██{reset}{dp}╔════╝{reset}{lilac}██{reset}{dp}║{reset}     {lilac}██{reset}{dp}║{reset}{lilac}████{reset}{dp}╗{reset}  {lilac}██{reset}{dp}║{reset}{lilac}██{reset}{dp}╔════╝{reset}   {dp}║{reset}
{dp}║{reset}     {lilac}██{reset}{dp}║{reset}   {lilac}██{reset}{dp}║{reset}{lilac}██{reset}{dp}╔{reset}{lilac}████{reset}{dp}╔{reset}{lilac}██{reset}{dp}║{reset}{lilac}█████{reset}{dp}╗{reset}  {lilac}██{reset}{dp}║{reset}     {lilac}██{reset}{dp}║{reset}{lilac}██{reset}{dp}╔{reset}{lilac}██{reset}{dp}╗{reset} {lilac}██{reset}{dp}║{reset}{lilac}█████{reset}{dp}╗{reset}     {dp}║{reset}
{dp}║{reset}     {lilac}██{reset}{dp}║{reset}   {lilac}██{reset}{dp}║{reset}{lilac}██{reset}{dp}║{reset}{dp}╚{reset}{lilac}██{reset}{dp}╔╝{reset}{lilac}██{reset}{dp}║{reset}{lilac}██{reset}{dp}╔══╝{reset}  {lilac}██{reset}{dp}║{reset}     {lilac}██{reset}{dp}║{reset}{lilac}██{reset}{dp}║{reset}{dp}╚{reset}{lilac}██{reset}{dp}╗{reset}{lilac}██{reset}{dp}║{reset}{lilac}██{reset}{dp}╔══╝{reset}     {dp}║{reset}
{dp}║{reset}     {lilac}██{reset}{dp}║{reset}   {lilac}██{reset}{dp}║{reset}{lilac}██{reset}{dp}║{reset} {dp}╚═╝{reset} {lilac}██{reset}{dp}║{reset}{lilac}███████{reset}{dp}╗{reset}{lilac}███████{reset}{dp}╗{reset}{lilac}██{reset}{dp}║{reset}{lilac}██{reset}{dp}║{reset} {dp}╚{lilac}████{reset}{dp}║{reset}{lilac}███████{reset}{dp}╗{reset}   {dp}║{reset}
{dp}║{reset}     {dp}╚═╝{reset}   {dp}╚═╝╚═╝{reset}     {dp}╚═╝╚══════{reset}{dp}╝╚══════╝╚═╝╚═╝{reset}  {dp}╚═══╝╚══════{reset}{dp}╝{reset}   {dp}║{reset}
{dp}║{reset}                                                                 {dp}║{reset}
{dp}║{reset}    {dg}╔{reset}{white}██████{reset}{dg}╗{reset}  {lilac}██{reset}{dp}╗{reset}{lilac}███{reset}{dp}╗{reset}   {lilac}███{reset}{dp}╗{reset} {lilac}█████{reset}{dp}╗{reset}  {lilac}██████{reset}{dp}╗{reset} {lilac}███████{reset}{dp}╗{reset}{lilac}███████{reset}{dp}║{reset}    {dp}║{reset}
{dp}║{reset}    {dg}╚════{white}██{reset}{dg}║{reset}  {lilac}██{reset}{dp}║{reset}{lilac}████{reset}{dp}╗{reset} {lilac}████{reset}{dp}║{reset}{lilac}██{reset}{dp}╔══{reset}{lilac}██{reset}{dp}╗{reset}{lilac}██{reset}{dp}╔════╝{reset} {lilac}██{reset}{dp}╔════╝{reset}{lilac}██{reset}{dp}╔════╝{reset}    {dp}║{reset}
{dp}║{reset}     {white}█████{reset}{dg}╔╝{reset}  {lilac}██{reset}{dp}║{reset}{lilac}██{reset}{dp}╔{reset}{lilac}████{reset}{dp}╔{reset}{lilac}██{reset}{dp}║{reset}{lilac}███████{reset}{dp}║{reset}{lilac}██{reset}{dp}║{reset}  {lilac}███{reset}{dp}╗{reset}{lilac}█████{reset}{dp}╗{reset}  {lilac}███████{reset}{dp}║{reset}    {dp}║{reset}
{dp}║{reset}    {white}██{reset}{dg}╔═══╝{reset}   {lilac}██{reset}{dp}║{reset}{lilac}██{reset}{dp}║╚{lilac}██{reset}{dp}╔╝{reset}{lilac}██{reset}{dp}║{reset}{lilac}██{reset}{dp}╔══{reset}{lilac}██{reset}{dp}║{reset}{lilac}██{reset}{dp}║{reset}   {lilac}██{reset}{dp}║{reset}{lilac}██{reset}{dp}╔══╝{reset}  {dp}╚════{lilac}██{reset}{dp}║{reset}    {dp}║{reset}
{dp}║{reset}    {white}███████{reset}{dg}╗{reset}  {lilac}██{reset}{dp}║{reset}{lilac}██{reset}{dp}║{reset} {dp}╚═╝{reset} {lilac}██{reset}{dp}║{reset}{lilac}██{reset}{dp}║{reset}  {lilac}██{reset}{dp}║╚{reset}{lilac}██████{reset}{dp}╔╝{reset}{lilac}███████{reset}{dp}╗{reset}{lilac}███████{reset}{dp}║{reset}    {dp}║{reset}
{dp}║{reset}    {dg}╚══════╝{reset}  {dp}╚═╝╚═╝{reset}     {dp}╚═╝╚═╝{reset}  {dp}╚═╝{reset} {dp}╚═════╝{reset} {dp}╚══════╝{reset}{dp}╚══════╝{reset}    {dp}║{reset}
{dp}║{reset}                                                                 {dp}║{reset}
{dp}║{reset}        Generate daily route maps from Google Timeline           {dp}║{reset}
{dp}║{reset}   EUPL-1.2, Copyright (c) 2026 David Hamber - Version {_pad_version(__version__)}{dp}║{reset}
{dp}║{reset}                                                                 {dp}║{reset}
{dp}╚═════════════════════════════════════════════════════════════════╝{reset}
"""
        print(banner)


def print_banner() -> None:
    """Display ASCII art banner with lilac and deep purple colors."""
    BannerPrinter.print_banner()
