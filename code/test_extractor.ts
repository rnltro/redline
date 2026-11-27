/* Quick extractor sanity test against the three fixture openings. */
import { extractEntities } from "../src/lib/redline/hybridClient";

const texts = [
  `This Mutual Non-Disclosure Agreement is entered into on November 15, 2026, between Lumen Robotics, Inc., a Delaware corporation with offices at 480 Harbor Point Drive, Suite 210, Portland, Oregon 97204 ("Disclosing Party A"), and Meridian Fabrication LLC, an Oregon limited liability company with offices at 2180 SE Belmont Street, Portland, Oregon 97214 ("Disclosing Party B").`,
  `This Loan Agreement is made on January 5, 2027 between Cascadia Credit Union, a state-chartered credit union with its principal office at 900 Capitol Boulevard, Boise, Idaho 83702 ("Lender"), and Kestrel Bakery LLC, an Idaho limited liability company located at 77 Larkspur Avenue, Boise, Idaho 83702 ("Borrower"), represented by Mr. Omar Haddad, Managing Member.`,
  `This Services Agreement is entered into effective March 1, 2027 by and between Northwind Design Studio, a Washington limited liability company with offices at 1510 12th Avenue, Seattle, Washington 98122 ("Contractor"), and Atlas Freight Co., a Washington corporation with offices at 401 Pier 69, Seattle, Washington 98104 ("Client"), as further described by Ms. Priya Raman, Principal, Northwind Design Studio (priya@northwind.example).`,
];

for (const t of texts) {
  const ents = extractEntities(t);
  console.log("----");
  console.log(ents.map((e) => `${e.replacement} = ${e.value}`).join("\n"));
}
