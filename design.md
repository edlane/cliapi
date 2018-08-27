# Design Considerations:
**Task:** port azuremetadata.pl (perl) to python

**Requirements:**
(Or rather, the Methodology used to Generate requirements):
1. compare azuremetadata CLI with the other metadata CLI modules for other cloud providers (ec2 and gce)
2. Identify and interview current users of metadata modules (Sean)

**Observations:**
- The 3 CLI metadata modules appear to have been written at 3 different times by 3 different
authors.
- Subtle and not so subtle differences exist in the CLI behaviors and output formats.
This requires developers to implement separate handlers and be aware of the idiosyncrasies
of each implementation.
- The GCE and EC2 modules both use getopt() and are largely familiar API except for
the returned results.
- Azure (the target of this port) is expectedly weird with different API, results, and configuration parameters
required (...and because it was written in Perl)
- It looks like the list of available and supported CLI query options for each cloud provider
has been added to over time.
To allow a new item to be queried from the CLI, the cloud module must also
be revised in order to access it.
- There is also a practice of adding other SUSE specific functions into the "cloud metadata"
rather than breaking them into separate CLIs. e.g "cloud-service", "billing-tag", etc.
- The meta-data collection of CLIs seems primarily to support automation pipelines elsewhere
in Enceladus and not meant exclusively for humans.
As such these CLIs are expected to have consistent behavior across all the meta-data CLIs
approaching that of an API rather than an ad-hoc query tool. Current best practice for API
publishers would seem to favor a "discoverable-style" APIs over traditional "man-page" described
ones".

**Proposal 1:**

- This is a mostly solved problem with Salt's grain module <https://github.com/saltstack/salt/blob/develop/salt/grains/metadata.py>
so implement azuremetadata entirely using Salt's metadata grains module 
- **Note:** Currently the Salt grains metadata module needs to be extended to support Azure. 
(estimate ~40 LOC for Azure support)
- add a "cloud-service" and other SUSE required functionality as custom grains modules (~20 LOC)
- replace other parts of Enceladus by Salt automation when duplicate functionality exists.
- develop custom Salt modules, runners, grains, states, beacons, .... to
implement Enceladus functionality where appropriate.
**(I am advised that "advocating this proposal would be _GREATLY OPPOSED_" -- so
dropping this proposal immediately")**

**alternative #2 to Proposal 1:**
- Allow salt grains to be called directly from CLI. This would allow salt grains to be called
as an executable module via **_salt-call_** (new functionality ~10 LOC)
- support other SUSE specific functions as separate **salt-call**-_able_ modules
rather than separate CLI programs.
This suffers from many of the objections of alternative #1 and would break existing consumers of
the old interface.

**Proposal 2:**

- Port azuremetadata.pl "as is" and create yet another slightly inconsistent CLI, but coded in Python instead.

**alternative #2 to Proposal 2:**

- Choose an existing cloud CLI (gce or ec2) and emulate that one as much as possible that same
behavior for **azuremetadata.py**
- For extra credit: Try to reconcile all the behavior differences in the various CLIs and
bring them back into compliance (at
least for one instance in time before the inevitable "code drift" takes hold)


**Proposal 3:**

- Create a common, extensible framework which will generate CLIs given a set of APIs
described as python functions using introspection.
- Enable backward compatibility by supporting all existing CLI options.
- Enable forward flexibility by adding a query-language extension which allows recently
added or previously unanticipated metadata API values to be queried.


### LOC Implementation Comparison for Proposal #3 above:
**Note:** Admittedly comparing developer editable lines of code between different implementations
is an unprecise and debatable activity but here is a worksheet used to prepare this report anyway...


https://docs.google.com/spreadsheets/d/1i_phns6QS3eCmsWFXWxxcafuNYXOEqG0ffxt6NHZysk/edit?usp=sharing

**Total Dev Edited LOC for Existing Implementation:**

**~2177 Total LOC** = ec2metadata + azuremetadata(perl) + gcemetadata


**Total Dev Edited LOC for Proposal #3 Implementation from above**

**~881 Total LOC** = cliapi(framework actual) + azure(plugin actual) + gce(plugin estimate) + ec2(plugin estimate)

