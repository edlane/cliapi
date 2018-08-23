#Design Considerations:
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
- The GCE and EC2 modules both use getopt() and are largely identical API except for
returned results.
- Azure is expectedly weird with different API, results, and configuration parameters
required (...and because it was written in Perl)
- It looks like the list of available and supported CLI query options for each cloud provider
has been added over time.
To allow a new item to be queried from the CLI, the cloud module must be revised first
in order to access it.
- There is a practice of adding other SUSE-cloud-provider specific functions along
with the "metadata" rather than breaking them into separate CLIs. e.g "cloud-service",
"billing-tag", etc.
- The meta-data collection of CLIs is primarily to support automation pipelines elsewhere in
Enceladus and as such should be expected to have a more consistent interface than tools
intended to be consumed only by humans.  Behavior across all the meta-data CLIs should be
more of an API than an ad-hoc query tool.

**Proposition 1:**

- This is mostly a solved problem with Salt's grain module [https://github.com/saltstack/salt/blob/develop/salt/grains/metadata.py]
so implement azuremetadata entirely using Salt's metadata grains module
- extend grains module to support azure cloud. (currently missing ~40 LOC)
- add "cloud-service" or other SUSE required functionality as custom grains (~20 LOC)
- replace other parts of Enceladus by Salt automation when duplicate functionality exists.
- develop custom Salt modules, runners, grains, states, beacons, .... as appropriate to
implement Enceladus functionality.
**(I am advised that "advocating this proposition would be my last official act" -- so
dropping this proposal immediately")**

**alternative #2 to Proposition 1:**
- Allow salt grains to be called directly from CLI. This would allow salt grains to be called
as an executable module via **_salt-call_** (new functionality ~10 LOC)
- support other SUSE specific functions as salt
This suffers from many of the objections of alternative #1 and would break consumers of
the old interface.

**Proposition 2:**

- Port "as is" and create yet another slightly inconsistent CLI, but coded in Python instead.

**alternative #2 to Proposition 2:**

- Choose an existing cloud CLI (gce or ec2) and emulate that one as much as possible that same
behavior for **azuremetadata.py**
- For extra credit: Try to reconcile all the behavior differences in the CLIs and bring them back into compatibility (at
least for one instance in time before the inevitable "code drift" takes hold) 


**Proposition 3:**

- Create a common, extensible framework which will generate CLIs given a set of APIs
described as python functions using introspection.
- Enable backward compatibility by supporting all existing CLI options.
- Enable forward flexibility by adding a query-language extension with allows recently
added or previously unanticipated metadata API values to be queried.

