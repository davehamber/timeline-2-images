"""ASCII art banner for timeline-2-images application."""

# ruff: noqa: E501
# pylint: disable=line-too-long


def print_banner():
    """Display ASCII art banner with lilac and deep purple colors."""
    lilac = "\033[38;2;200;162;200m"  # Light lilac/lavender
    deep_purple = "\033[38;2;138;43;226m"  # Deep purple (blue-violet)
    white = "\033[38;2;255;255;255m"  # White for "2" block
    dark_grey = "\033[38;2;100;100;100m"  # Dark grey for "2" drop shadow
    reset = "\033[0m"

    banner = f"""
{deep_purple}╔═════════════════════════════════════════════════════════════════╗{reset}
{deep_purple}║{reset}                                                                 {deep_purple}║{reset}
{deep_purple}║{reset}  {lilac}████████{reset}{deep_purple}╗{reset}{lilac}██{reset}{deep_purple}╗{reset}{lilac}███{reset}{deep_purple}╗{reset}   {lilac}███{reset}{deep_purple}╗{reset}{lilac}███████{reset}{deep_purple}╗{reset}{lilac}██{reset}{deep_purple}╗{reset}     {lilac}██{reset}{deep_purple}╗{reset}{lilac}███{reset}{deep_purple}╗{reset}   {lilac}██{reset}{deep_purple}╗{reset}{lilac}███████{reset}{deep_purple}╗{reset}   {deep_purple}║{reset}
{deep_purple}║{reset}  {deep_purple}╚══{lilac}██{reset}{deep_purple}╔══╝{reset}{lilac}██{reset}{deep_purple}║{reset}{lilac}████{reset}{deep_purple}╗{reset} {lilac}████{reset}{deep_purple}║{reset}{lilac}██{reset}{deep_purple}╔════╝{reset}{lilac}██{reset}{deep_purple}║{reset}     {lilac}██{reset}{deep_purple}║{reset}{lilac}████{reset}{deep_purple}╗{reset}  {lilac}██{reset}{deep_purple}║{reset}{lilac}██{reset}{deep_purple}╔════╝{reset}   {deep_purple}║{reset}
{deep_purple}║{reset}     {lilac}██{reset}{deep_purple}║{reset}   {lilac}██{reset}{deep_purple}║{reset}{lilac}██{reset}{deep_purple}╔{reset}{lilac}████{reset}{deep_purple}╔{reset}{lilac}██{reset}{deep_purple}║{reset}{lilac}█████{reset}{deep_purple}╗{reset}  {lilac}██{reset}{deep_purple}║{reset}     {lilac}██{reset}{deep_purple}║{reset}{lilac}██{reset}{deep_purple}╔{reset}{lilac}██{reset}{deep_purple}╗{reset} {lilac}██{reset}{deep_purple}║{reset}{lilac}█████{reset}{deep_purple}╗{reset}     {deep_purple}║{reset}
{deep_purple}║{reset}     {lilac}██{reset}{deep_purple}║{reset}   {lilac}██{reset}{deep_purple}║{reset}{lilac}██{reset}{deep_purple}║{reset}{deep_purple}╚{reset}{lilac}██{reset}{deep_purple}╔╝{reset}{lilac}██{reset}{deep_purple}║{reset}{lilac}██{reset}{deep_purple}╔══╝{reset}  {lilac}██{reset}{deep_purple}║{reset}     {lilac}██{reset}{deep_purple}║{reset}{lilac}██{reset}{deep_purple}║{reset}{deep_purple}╚{reset}{lilac}██{reset}{deep_purple}╗{reset}{lilac}██{reset}{deep_purple}║{reset}{lilac}██{reset}{deep_purple}╔══╝{reset}     {deep_purple}║{reset}
{deep_purple}║{reset}     {lilac}██{reset}{deep_purple}║{reset}   {lilac}██{reset}{deep_purple}║{reset}{lilac}██{reset}{deep_purple}║{reset} {deep_purple}╚═╝{reset} {lilac}██{reset}{deep_purple}║{reset}{lilac}███████{reset}{deep_purple}╗{reset}{lilac}███████{reset}{deep_purple}╗{reset}{lilac}██{reset}{deep_purple}║{reset}{lilac}██{reset}{deep_purple}║{reset} {deep_purple}╚{lilac}████{reset}{deep_purple}║{reset}{lilac}███████{reset}{deep_purple}╗{reset}   {deep_purple}║{reset}
{deep_purple}║{reset}     {deep_purple}╚═╝{reset}   {deep_purple}╚═╝╚═╝{reset}     {deep_purple}╚═╝╚══════{reset}{deep_purple}╝╚══════╝╚═╝╚═╝{reset}  {deep_purple}╚═══╝╚══════{reset}{deep_purple}╝{reset}   {deep_purple}║{reset}
{deep_purple}║{reset}                                                                 {deep_purple}║{reset}
{deep_purple}║{reset}    {dark_grey}╔{reset}{white}██████{reset}{dark_grey}╗{reset}  {lilac}██{reset}{deep_purple}╗{reset}{lilac}███{reset}{deep_purple}╗{reset}   {lilac}███{reset}{deep_purple}╗{reset} {lilac}█████{reset}{deep_purple}╗{reset}  {lilac}██████{reset}{deep_purple}╗{reset} {lilac}███████{reset}{deep_purple}╗{reset}{lilac}███████{reset}{deep_purple}║{reset}    {deep_purple}║{reset}
{deep_purple}║{reset}    {dark_grey}╚════{white}██{reset}{dark_grey}║{reset}  {lilac}██{reset}{deep_purple}║{reset}{lilac}████{reset}{deep_purple}╗{reset} {lilac}████{reset}{deep_purple}║{reset}{lilac}██{reset}{deep_purple}╔══{reset}{lilac}██{reset}{deep_purple}╗{reset}{lilac}██{reset}{deep_purple}╔════╝{reset} {lilac}██{reset}{deep_purple}╔════╝{reset}{lilac}██{reset}{deep_purple}╔════╝{reset}    {deep_purple}║{reset}
{deep_purple}║{reset}     {white}█████{reset}{dark_grey}╔╝{reset}  {lilac}██{reset}{deep_purple}║{reset}{lilac}██{reset}{deep_purple}╔{reset}{lilac}████{reset}{deep_purple}╔{reset}{lilac}██{reset}{deep_purple}║{reset}{lilac}███████{reset}{deep_purple}║{reset}{lilac}██{reset}{deep_purple}║{reset}  {lilac}███{reset}{deep_purple}╗{reset}{lilac}█████{reset}{deep_purple}╗{reset}  {lilac}███████{reset}{deep_purple}║{reset}    {deep_purple}║{reset}
{deep_purple}║{reset}    {white}██{reset}{dark_grey}╔═══╝{reset}   {lilac}██{reset}{deep_purple}║{reset}{lilac}██{reset}{deep_purple}║╚{lilac}██{reset}{deep_purple}╔╝{reset}{lilac}██{reset}{deep_purple}║{reset}{lilac}██{reset}{deep_purple}╔══{reset}{lilac}██{reset}{deep_purple}║{reset}{lilac}██{reset}{deep_purple}║{reset}   {lilac}██{reset}{deep_purple}║{reset}{lilac}██{reset}{deep_purple}╔══╝{reset}  {deep_purple}╚════{lilac}██{reset}{deep_purple}║{reset}    {deep_purple}║{reset}
{deep_purple}║{reset}    {white}███████{reset}{dark_grey}╗{reset}  {lilac}██{reset}{deep_purple}║{reset}{lilac}██{reset}{deep_purple}║{reset} {deep_purple}╚═╝{reset} {lilac}██{reset}{deep_purple}║{reset}{lilac}██{reset}{deep_purple}║{reset}  {lilac}██{reset}{deep_purple}║╚{reset}{lilac}██████{reset}{deep_purple}╔╝{reset}{lilac}███████{reset}{deep_purple}╗{reset}{lilac}███████{reset}{deep_purple}║{reset}    {deep_purple}║{reset}
{deep_purple}║{reset}    {dark_grey}╚══════╝{reset}  {deep_purple}╚═╝╚═╝{reset}     {deep_purple}╚═╝╚═╝{reset}  {deep_purple}╚═╝{reset} {deep_purple}╚═════╝{reset} {deep_purple}╚══════╝{reset}{deep_purple}╚══════╝{reset}    {deep_purple}║{reset}
{deep_purple}║{reset}                                                                 {deep_purple}║{reset}
{deep_purple}║{reset}        Generate daily route maps from Google Timeline           {deep_purple}║{reset}
{deep_purple}║{reset}                                                                 {deep_purple}║{reset}
{deep_purple}╚═════════════════════════════════════════════════════════════════╝{reset}
"""
    print(banner)
