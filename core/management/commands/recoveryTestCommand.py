from django.core.management.base import BaseCommand


# python manage.py recoveryTestCommand
class Command(BaseCommand):
    help = "Run recoveryTestCommand"

    def add_arguments(self, parser):
        parser.add_argument(
            "--param",
            type=str,
            help="Param",
        )



    def handle(self, *args, **options):
        param = options.get("param")
        print("Disabled")
        exit()

        # хочу восстановить все контакты из старой папки
        from exchange.services.ExchangeService import ExchangeService
        from exchange.services.ExchangeUpdatesService import ExchangeUpdatesService
        folder = ExchangeService.get_exchange_folder(folder_path_extra="Contasts Shared DB/Test Folder/Company Contacts: Dust Busters Plus LLC")
        print(folder)
        emails_list = [
            '19justingriffis87@gmail.com',
            '1actionjacksonw@gmail.com',
            '1ethan.rogers@gmail.com',
            '24jgasca@gmail.com',
            '80ggabriel10@gmail.com',
            'Carinashine123@gmail.com',
            'Cooper.c.petersen@gmail.com',
            'Dahbgo02@gmail.com',
            'Joshcollins872@gmail.com',
            'Pnaperry@gmail.com',
            'Quinten7777@gmail.com',
            'SirShaynee@gmail.com',
            'Test11@Automation.com',
            'aasghar747@gmail.com',
            'abdielsemail@gmail.com',
            'abrambillings@gmail.com',
            'adparker70@gmail.com',
            'agg003@morningside.edu',
            'agonzalc9@gmail.com',
            'aguilariiiesteban@gmail.com',
            'agustin.gabriel.gonzalez@gmail.com',
            'ahmadaimaq302@gmail.com',
            'aiden.prows@icloud.com',
            'aidenmyhre2@gmail.com',
            'albertlund@gmail.com',
            'alexanderncoe1997@gmail.com',
            'alexisvictoriano@icloud.com',
            'allan.barrera2006@gmail.com',
            'am559u1313@gmail.com',
            'amacgregor15973@gmail.com',
            'amayaalvaro2@gmail.com',
            'amsanchez202020@gmail.com',
            'andrelsouzaca@gmail.com',
            'andresbluesenthusiast@gmail.com',
            'andrew.c.barrientos@gmail.com',
            'andrew.fscheyer@gmail.com',
            'andrewostrihon@gmail.com',
            'andrusethan7@gmail.com',
            'angelacostaa710@gmail.com',
            'angelrangeltobro@gmail.com',
            'anthony.nguyen1002@gmail.com',
            'antonchacon05@gmail.com',
            'antoniofoulks@gmail.com',
            'ap3942281@gmail.com',
            'ap3ters1904@gmail.com',
            'archibaldpuddin@gmail.com',
            'arh1988@yahoo.com',
            'arlobautista21@icloud.com',
            'arreguinjoseph@gmail.com',
            'arturojaracuaro16@gmail.com',
            'austin.laskaris@k12csd.us',
            'awhite12@radford.edu',
            'aydenprater42@gmail.com',
            'bDLiS3kvCHUAivkOaSwg',
            'baldwinamos93@gmail.com',
            'baylorhanifin@gmail.com',
            'bengooltz123a@gmail.com',
            'benhumphrey30@gmail.com',
            'bennyjc04@gmail.com',
            'bhebeisen@live.com',
            'bigm4033@gmail.com',
            'blk_bam@yahoo.com',
            'bmax57901@gmail.com',
            'bootonconner@gmail.com',
            'brad.kline39@yahoo.com',
            'bradyfire05@gmail.com',
            'braidendockins18@gamil.com',
            'brettbernier123@gmail.com',
            'brettroymiiller@gmail.com',
            'broganamer@gmail.com',
            'browneli007@icloud.com',
            'brussell3218@icloud.com',
            'brydenvalois15@gmail.com',
            'buchs.james@gmail.com',
            'buddasmain@gmail.com',
            'burnell.ed@gmail.com',
            'buttmunch021@gmail.com',
            'byonrobert@gmail.com',
            'byrdclarance@gmail.com',
            'caison117echols@gmail.com',
            'calebsmylie21@gmail.com',
            'camwalt01@yahoo.com',
            'canulnoe406@gmail.com',
            'carlosceronmartinez@icloud.com',
            'carson8204@yahoo.com',
            'celestiabeats@live.com',
            'chadcroucher0102@gmail.com',
            'chaparromatthew41@mygya.com',
            'charliecappin02@gmail.com',
            'charlottehorn915@gmail.com',
            'chris.snortland@hotmail.com',
            'chrishubbard0105@gmail.com',
            'christian.m.soden@gmail.com',
            'chuymap12@gmail.com',
            'ckoivu05@gmail.com',
            'ckrohlow44@gmail.com',
            'clapperl025@gmail.com',
            'clarkjsessions6@gmail.com',
            'cobiobrien21@gmail.com',
            'coleread522@gmail.com',
            'colinnewgard@icloud.com',
            'colinsaldana444@gmail.com',
            'cooper.c.petersen@gmail.com',
            'cristianrmz2005@gmail.com',
            'culbreathtyreke680@gmail.com',
            'cvanvaler@comcast.net',
            'damian.r.medina1705@gmail.com',
            'danbak2003@yahoo.com',
            'darechar8@gmail.com',
            'dariuslam04@gmail.com',
            'dartwhiteloo@gmail.com',
            'datboicam1996@gmail.com',
            'dav.per017@gmail.com',
            'daveyflo4@gmail.com',
            'daveysanch@gmail.com',
            'davida4959@gmail.com',
            'davidbungardner@gmail.com',
            'db041513@gmail.com',
            'dbelus1996@gmail.com',
            'dblotwitch@gmail.com',
            'dbrodnax01@yahoo.com',
            'dchavarria039@gmail.com',
            'derskin2012@gmail.com',
            'dillonrangel1@gmail.com',
            'djmeadows41@gmail.com',
            'dkenner588@icloud.com',
            'dmiller313@icloud.com',
            'dmrcswells@gmail.com',
            'dmrs316@gmail.com',
            'dominiccalderon578@gmail.com',
            'doxphilpott@gmail.com',
            'dprince935@gmail.com',
            'dustincordeiro05@gmail.com',
            'dweltathlete1@gmail.com',
            'dylancal215@gmail.com',
            'e.is.real1216@gmail.com',
            'eaton.btandon7@gmail.com',
            'ebowles23@icloud.com',
            'edwardgwilliams41@gmail.com',
            'eggsontoast889@gmail.com',
            'eli768483@gmail.com',
            'eliflamoe@gmail.com',
            'elijah.cordero1230@gmail.com',
            'elijah.ghulam@gmail.com',
            'elishapichardo1@gmail.com',
            'elliotcornejo44@gmail.com',
            'elvelazquez960@icloud.com',
            'enriquesustaita024@icloud.com',
            'epachuca414@icloud.com',
            'ernestoalain28@gmail.com',
            'esjdevjn316@gmail.com',
            'ethanparker0731@gmail.com',
            'ethanscotthanus@gmail.com',
            'ezekielluna808@gmail.com',
            'flinderscameron@gmail.com',
            'floreslx280@gmail.com',
            'franciscodelarosa785@gmail.com',
            'franklinjones071@gmail.com',
            'frankquon13@gmail.com',
            'ft100overall23@icloud.com',
            'gabster101204@gmail.com',
            'gameps.thomas@gmail.com',
            'garrettwilliams203@gmail.com',
            'garronhanks@gmail.com',
            'gavinskyler55@gmail.com',
            'geralddevoe00@gmail.com',
            'glantz.tyler@gmail.com',
            'glokkeith@gmail.com',
            'goddardbraeden80@gmail.com',
            'goybailey@gmail.com',
            'graceslynnsia@gmail.com',
            'hahn2474@gmail.com',
            'harrisfamjt@gmail.com',
            'hcarv004@gmail.com',
            'hclukey256@gmail.com',
            'heathbozworth7@gmail.com',
            'heflin.blake.k@gmail.com',
            'heflir.blake.k@gmail.com',
            'hendrixlawson05@gmail.com',
            'henryguts878@gmail.com',
            'hiphopsippy@icloud.com',
            'hudhayfahal@gmail.com',
            'hunterhemphill707@gmail.com',
            'hunterhottle52142@gmail.com',
            'huntrerobinson762@gmail.com',
            'iainmahoney04@gmail.com',
            'ihaveacrushonshay@gmail.com',
            'ijwhwork@gmail.com',
            'indy_5050@icloud.com',
            'isaiah.alvarez1223@gmail.com',
            'isaiahwaitkus@gmail.com',
            'isairios330@gmail.com',
            'isilelimasi691@gmail.com',
            'isnagrsn@yahoo.com',
            'itzmalachi@gmail.com',
            'ivan.bocanegra1@icloud.com',
            'ivanj000@icloud.com',
            'jac2281395@maricopa.edu',
            'jackkilbride@icloud.com',
            'jacobbissonette@gmail.com',
            'jacobroth2002@gmail.com',
            'jacobskalin@icloud.com',
            'jacqueline.lopezromero@gmail.com',
            'jadenday90@gmail.com',
            'jadingeorge321@gmail.com',
            'jakefarlee@gmail.com',
            'jamesbuttitta1@gmail.com',
            'jamesj.hour@gmail.com',
            'jamesmark1116@gmail.com',
            'jaredrettig30@yahoo.com',
            'jaredsalinas25@gmail.com',
            'jasonweber420@icloud.com',
            'jawill0409@gmail.com',
            'jctrinchere1@gmail.com',
            'jessnorita670@gmail.com',
            'jgravestocker@gmail.com',
            'jgsimonini01@gmail.com',
            'jhersongomora0@gmail.com',
            'jibransoto21@gmail.com',
            'jimmysalasjr2424@yahoo.com',
            'jlopezjudo321@gmail.com',
            'jonathanadsit@gmail.com',
            'jonathancano12345678@gmail.com',
            'jonathanhickman6969@gmail.com',
            'joonhyunga@gmail.com',
            'jorgecornejo9999@gmail.com',
            'joseguevara.3924@gmail.com',
            'joseph.joey.thomas@gmail.com',
            'josephgates2005@gmail.com',
            'josephmbellardo@gmail.com',
            'joshcollins872@gmail.com',
            'joshuabarran@gmail.com',
            'joshuahunt5595@gmail.com',
            'jpspringer313@duck.com',
            'juarezadrian799@gmail.com',
            'jules@dwellersoul.com',
            'julius.kilpatrick@gmail.com',
            'junjames74@gmail.com',
            'justinwinterling33@gmail.com',
            'jwpalmeriii@gmail.com',
            'kacymorse@gmail.com',
            'kaden.fansler@gmail.com',
            'kadenhowe246@gmail.com',
            'kadenjames4@gmail.com',
            'kallweitnoah1@gmail.com',
            'kanemccallan10@gmail.com',
            'karmen.aldaco@gmail.com',
            'karsonhaysbert@gmail.com',
            'kaylalim911@gmail.com',
            'kdill490@gmail.com',
            'kduke932@gmail.com',
            'keagan.schnoor@gmail.com',
            'kellencohen4@gmail.com',
            'kellzhytrek@gmail.com',
            'kgubler22@gmail.com',
            'kieran.gilbert@yahoo.com',
            'kilsins4@gmail.com',
            'kimsy0406@yahoo.com',
            'kmart081299@gmail.com',
            'konnerbellgeyler@icloud.com',
            'kristoferpowell29@gmail.com',
            'kylantopp@gmail.com',
            'kylebennington27@gmail.com',
            'kyledchang@gmail.com',
            'l.forcino12@gmail.com',
            'l0gancarpenter@icloud.com',
            'lancewilli04@gmail.com',
            'leblurp@gmail.com',
            'legacy.lopez15@gmail.com',
            'lemarionm47@gmail.com',
            'leo87.cortez@gmail.com',
            'leonardomendoza047@gmail.com',
            'levifeltes@gmail.com',
            'lewis.d.09990@gmail.com',
            'lnini8481@gmail.com',
            'lorenzoftw101@gmail.com',
            'louhanson681@gmail.con',
            'lukecf0112@gmail.com',
            'm_gmarcello083@gmail.com',
            'macelav11@gmail.com',
            'marlicvalentine@gmail.com',
            'marron.matte@gmail.com',
            'masonrowan926@gmail.com',
            'matthewaddison223@gmail.com',
            'matthewczipper@gmail.com',
            'mayhem47mack@gmail.com',
            'megan.mcentee@me.com',
            'meghanelric@gmail.com',
            'mfeakerqc@yahoo.com',
            'michaelbond3209@gmail.com',
            'michaelfenner05@outlook.com',
            'millingtondustin@gmail.com',
            'mipoderes@gmail.com',
            'mkl98@ymail.com',
            'mmattcow@gmail.com',
            'mochajoeshizzle@icloud.com',
            'monroe.mozee@icloud.com',
            'msheehan@gowva.org',
            'munoz.jeremiahp@gmail.com',
            'myrealnameisterrence@gmail.com',
            'nadjibaimene41@gmail.com',
            'nate.rogers06@gmail.com',
            'newbalance641@gmail.com',
            'nicholas.cadena0505@gmail.com',
            'nicolasagtern@gmail.com',
            'nikkogomez3131@gmail.com',
            'olearysean32@gmail.com',
            'oliverstudebaker3@gmail.com',
            'oregon.sav.503@gmail.com',
            'orionjr.cud@gmail.com',
            'orrinhthomas@cox.net',
            'osorioedgar7@gmail.com',
            'paige.michalski@icloud.com',
            'patrickdemlax@gmail.com',
            'pedroluquin00@gmail.com',
            'peeblesbraylon@gmail.com',
            'peralesisaac00@gmail.com',
            'perezgiovanni238@gmail.com',
            'pernellsylvester@icloud.com',
            'petersonronnie04@gmail.com',
            'poppystorm07@gmail.com',
            'preston.hatkow@gmail.com',
            'qmccornack@gmail.com',
            'qxwby5@gmail.com',
            'raddaaron@gmail.com',
            'ralund@outlook.com',
            'rarnold336@gmail.com',
            'rashidahmadzai2030@gmail.com',
            'raulrios132@yahoo.com',
            'rcontreras100903@gmail.com',
            'rdschmollinger@gmail.com',
            'ridgelray9@gmail.com',
            'rileyzeglin@gmail.com',
            'robert.chavez511@gmail.com',
            'rolanbr4@gmail.com',
            'rome.hinojosa@hotmail.con',
            'ronihennessey9@gmail.com',
            'ronniecardiel7734@gmail.com',
            'rsan.response@gmail.com',
            'ryguyboyd@gmail.com',
            'sabillonsgt1@gmail.com',
            'sageriver984@gmail.com',
            'salcedojunior720@gmail.com',
            'samanthaaugust72@gmail.com',
            'samuelalexander132019@outlook.com',
            'samuelgauthier2020@gmail.com',
            'samuelk6285@gmail.com',
            'sawyer.p.mccall@gmail.com',
            'seamanjon@gmail.com',
            'seanw888willow@gmail.com',
            'sebastianmorae02@gmail.com',
            'sethkvamme@gmail.com',
            'shauntaenight21@gmail.com',
            'shefftergrrr@gmail.com',
            'sherlyngar2006@gmail.com',
            'shiloweston97@gmail.com',
            'sias.gavin@yahoo.com',
            'sirshaynee@gmail.com',
            'smonreal678@gmail.com',
            'spencerroley@gmail.com',
            'sseas2423@yahoo.com',
            'st20078891@gmail.com',
            'starrettquarry@icloud.com',
            'tallanderek@outlook.com',
            'talvis5150@icloud.com',
            'tanner.caldwell@icloud.com',
            'tannerbraun1776@gmail.com',
            'tannerbridgeman@gmail.com',
            'tedpierre134@gmail.com',
            'test10@automation.com',
            'test10aa@automation.com',
            'test11@automation.com',
            'test2@automation.com',
            'test@test.com',
            'tgohlke@yahoo.com',
            'thomasnthomas3@gmail.com',
            'thomasward6789@gmail.com',
            'tmp1023@gmail.com',
            'tonyfold85@gmail.com',
            'tonymontana23z@icloud.com',
            'tp.lucas74@gmail.com',
            'tracymason516@gmail.com',
            'trevor.mcm1@gmail.com',
            'trevorbenallie@gmail.com',
            'trinidadkeven99@gmail.com',
            'tyflo310@gmail.com',
            'tyler.deangriff33@gmail.com',
            'tyleracrites@gmail.com',
            'tylerhead254@gmail.com',
            'tyranttypical@gmail.com',
            'tyrohlman@gnail.com',
            'upshaw3rdkevin@gmail.com',
            'urielsantacruz85@gmail.com',
            'vanillagorilla249@gmail.com',
            'velardezgm@gmail.com',
            'vicmbride@gmail.com',
            'villakevn@gmail.com',
            'vjsmith579@gmail.com',
            'vukujavec@gmail.com',
            'waynejohnstonx@gmail.com',
            'wightlight21@gmail.com',
            'williamgalloway11@gmail.com',
            'wolterr36@gmail.com',
            'wpmatt44@gmail.com',
            'yepcrawford@gmail.com',
            'yung.jr1011@gmail.com',
            'zach.hoydic@yahoo.com',
            'zachpt222@gmail.com',
            'zanehall0463@yahoo.com',
            'zbarnes8@icloud.com',
            'zekearriaga96@gmail.com',
            'zepolbur@gmail.com',
            'zinfante25@gmail.com',
            'zsolso876@gmail.com'
        ]
        for email in emails_list:
            res_email = ExchangeUpdatesService.do_update_from_exchange_by_email(email=email, ignore_diff_properties=True, folder=folder)

            print(res_email)

        print("DONE")
        exit()

    def handle2(self, *args, **options):
        param = options.get("param")
        print("Disabled")
        exit()

        # хочу восстановить все контакты из старой папки
        # from exchange.services.ExchangeService import ExchangeService
        from exchange.services.ExchangeUpdatesService import ExchangeUpdatesService
        # folder = ExchangeService.get_exchange_folder(folder_path_extra="Contasts Shared DB/Test Folder/Company Contacts: Dust Busters Plus LLC")
        # print(folder)
        emails_list = [
# "21reedhoganj@gmail.com",
# "24miley.cameron@gmail.com",
# "aaronahumada1234@gmail.com",
# "adamstrickler808@gmail.com",
# "agosnell2007@gmail.com",
# "aidan.linnabary@icloud.com",
# "aidancooper913@gmail.com",
# "alejandromeono12@gmail.com",
# "alexandermurray011507@gmail.com",
# "ap3ters1904@gmail.com",
# "arh1988@yahoo.com",
# "arlomartin25@gmail.com",
# "ashaver315@gmail.com",
# "ashlynfh4@icloud.com",
# "atbeebe98@gmail.com",
# "bakerlamar5556@icloud.com",
# "bcasiquito03@gmail.com",
# "bebo33414@gmail.com",
# "bensenffners@gmail.com",
# "blaynespradling2002@gmail.com",
# "brandenremly@gmail.com",
# "brandon.tribuiani@gmail.com",
# "braxton.a.f.123@gmail.com",
# "brendadersanchez07@gmail.com",
# "brianmelvin673@gmail.com",
# "bundycows@gmail.com",
# "cadeh454@gmail.com",
# "caitlin3debra2@gmail.com",
# "cameronott02@icloud.com",
# "cameronsouza03@gmail.com",
# "canulnoe406@gmail.com",
# "carson8204@yahoo.com",
# "cashmoneymoves2019@gmail.com",
# "chasescheurn@icloud.com",
# "christianbruno007@gmail.com",
# "cjmags212@gmail.com",
# "colinisherwood2@gmail.com",
# "colinnewgard@icloud.com",
# "colinsul07@gmail.com",
# "coltwest94@gmail.com",
# "criztiancenteno1503@gmail.com",
# "cvanvaler@comcast.net",
# "Cyruscarey1@gmail.com",
# "darinrichards1000@icloud.com",
# "dariuslam04@gmail.com",
# "davidide1278@gmail.com",
# "devinbuckhout@comcast.net",
# "dhuffman700@gmail.com",
# "dillon.ian.86@gmail.com",
# "dparkers02@icloud.com",
# "dustin.berg997@gmail.com",
# "eli.felton220@gmail.com",
# "elijahjhull@gmail.com",
# "elijahmaisey15@gmail.com",
# "eth.4012.eth@gmail.com",
# "ethanfalkner06@gmail.com",
# "evanmelman@icloud.com",
# "fernandovillalobos1204@gmail.com",
# "fkscreamingreels@gmail.com",
# "gabrieltiefenback5@gmail.com",
# "gavinskyler55@gmail.com",
# "gerrettweaver@yahoo.com",
# "giancarlococcia1220@gmail.com",
# "gioali187@gmail.com",
# "haganandrew131@gmail.com",
# "haydenburgess2001@gmail.com",
# "hcortezri1111@gmail.com",
# "hudhayfahal@gmail.com",
# "iabzingg@icloud.com",
# "isa830iah@icloud.com",
# "isaacmontes18@gmail.com",
# "jamesj.hour@gmail.com",
# "jamesnorwood3rd@gmail.com",
# "jamjakob.a.martin@gmail.com",
# "jarinhuson@gmail.com",
# "jasoniamyourson@icloud.com",
# "jasonweber420@icloud.com",
# "jcarlosilhy@gmail.com",
# "jesiahrebolledo4@gmail.com",
# "jesseliesegang06@gmail.com",
# "jesuscenteno068@gmail.com",
# "jethro.f@hotmail.com",
# "jettakabug@yahoo.com",
# "jimmy.jecino@gmail.com",
# "jimmybright979@gmail.com",
# "jnstevenson71@gmail.com",
# "johncavalier606@gmail.com",
# "jorgealvarado8612@gmail.com",
# "jrg2504@icloud.com",
# "jroginiel20@gmail.com",
# "js7050229@gmail.com",
# "jwilcken181@gmail.com",
# "jwpalmeriii@gmail.com",
# "kadenmi17@gmail.com",
# "kawaiipanda2619@gmail.com",
# "kellogglandon276@gmail.com",
# "kfischer0129@icloud.com",
# "kilsins4@gmail.com",
# "kylebrooks2301@gmail.com",
# "kyleconstantin4@gmail.com",
# "lance.mariscal@hotmail.com",
# "liamlara040@gmail.com",
# "liamnum15@gmail.com",
# "logan.boverhof@gmail.com",
# "logandelehanty@gmail.com",
# "lombardichayce@gmail.com",
# "m.ibiam2003@gmail.com",
# "marcosresendizr@gmail.com",
# "marcuscook2727@gmail.com",
# "markgarcia2002a@gmail.com",
# "markstites01@hotmail.com",
# "mattmcrae67@gmail.com",
# "mauricioveraworkmaul@gmail.com",
# "mbroach280@gmail.com",
# "memo.gorilla55@gmail.com",
# "mhatlastcheck@gmail.com",
# "michael.frere61@gmail.com",
# "milumung2004@gmail.com",
# "mitchnorman615@gmail.com",
# "mitchyjacquay@gmail.com",
# "mkandil23@gmail.com",
# "mr0520506@gmail.com",
# "mychalhortert@gmail.com",
# "newbalance641@gmail.com",
# "nicholasdandar@gmail.com",
# "nikitasbitnev2019@gmail.com",
# "oscargonzalez82505@icloud.com",
# "owentdixon@gmail.com",
# "ozromoon@gmail.com",
# "patric.sipes@gmail.com",
# "pealingyalvarado91@gmail.com",
# "prestonarouse@gmail.com",
# "rashidahmadzai2030@gmail.com",
# "renty.mike@gmail.com",
# "richardmoulton2901@gmail.com",
# "riftsandvalleys@gmail.com",
# "robbiewwalton04@gmail.com",
# "robert.chavez511@gmail.com",
# "rocklinscout@gmail.com",
# "ryantisocial@gmail.com",
# "ryder.bishop05@outlook.com",
# "rymerr9@gmail.com",
# "samuelalexander132019@outlook.com",
# "samuelgauthier2020@gmail.com",
# "sanchezevan382@gmail.com",
# "scott.wade6519@gmail.com",
# "sebastianmorae02@gmail.com",
# "selectingocean5@gmail.com",
# "sergiolopez12200@gmail.com",
# "sezemercy0408@gmail.com",
# "sotorichard444@gmail.com",
# "stevn078@gmail.com",
# "stratosalius4@gmail.com_duplicate_1",
# "sublimetx01@gmail.com",
# "sylaswodowski27@gmail.com",
# "tafoyachris27@gmail.com",
# "tannerkle156@gmail.com",
# "thehulk821@gmail.com",
# "thomasdonaty1@gmail.com",
# "tmarchetti@att.net",
# "tmp1023@gmail.com",
# "tylonharrison123@icloud.com",
# "tyronemw5@gmail.com",
# "vasilythegreek@gmail.com",
# "velardezgm@gmail.com",
# "velascorafael578@gmail.com",
# "victorjwarndt@gmail.com",
# "victorrodriguezar1@gmail.com",
# "vinnypaddock11@gmail.com",
# "viviana0205@icloud.com",
# "waltersr2099@gmail.com",
# "williamadesch23@gmail.com",
# "wolfshady377@gmail.com",
# "wyntersaito0@gmail.com",
# "ybedoya624@gmail.com",
# "zachgibson5555@gmail.com",
# "zak.bt.gregg@gmail.com_duplicate_1",
# "zayzaykiloalan@gmail.com",
# "zbarnes8@icloud.com",

        ]
        for email in emails_list:
            # For Exchange
            # res_email = ExchangeUpdatesService.do_update_from_exchange_by_email(email=email, ignore_diff_properties=True)
            # print(res_email)

            # For Privser
            print("email: ", email)
            cont = PrivserAPI2Service().get_contacts_by_email(email=email)
            contact_id = cont.get("id")
            print("cont: ", contact_id)
            PrivserUpdatesService.update_all_fields_from_contact_id(contact_id=contact_id, ignore_diff_properties=False)

        print("DONE")
        exit()


problems = [
"19justingriffis87@gmail.com",
"24jgasca@gmail.com",
"80ggabriel10@gmail.com",
"aasghar747@gmail.com",
"agg003@morningside.edu",
"aguilariiiesteban@gmail.com",
"ahmadaimaq302@gmail.com",
"aiden.prows@icloud.com",
"aidenmyhre2@gmail.com",
"alexisvictoriano@icloud.com",
"allan.barrera2006@gmail.com",
"am559u1313@gmail.com",
"amayaalvaro2@gmail.com",
"amsanchez202020@gmail.com",
"andrelsouzaca@gmail.com",
"andrewostrihon@gmail.com",
"andrusethan7@gmail.com",
"angelacostaa710@gmail.com",
"angelrangeltobro@gmail.com",
"anthony.nguyen1002@gmail.com",
"antonchacon05@gmail.com",
"ap3942281@gmail.com",
"ap3ters1904@gmail.com",
"archibaldpuddin@gmail.com",
"arlobautista21@icloud.com",
"arturojaracuaro16@gmail.com",
"austin.laskaris@k12csd.us",
"aydenprater42@gmail.com",
"bDLiS3kvCHUAivkOaSwg",
"baldwinamos93@gmail.com",
"bengooltz123a@gmail.com",
"bennyjc04@gmail.com",
"bigm4033@gmail.com",
"blk_bam@yahoo.com",
"bmax57901@gmail.com",
"bootonconner@gmail.com",
"bradyfire05@gmail.com",
"braidendockins18@gamil.com",
"brettbernier123@gmail.com",
"browneli007@icloud.com",
"brussell3218@icloud.com",
"buchs.james@gmail.com",
"buddasmain@gmail.com",
"burnell.ed@gmail.com",
"buttmunch021@gmail.com",
"byonrobert@gmail.com",
"caison117echols@gmail.com",
"camwalt01@yahoo.com",
"canulnoe406@gmail.com",
"carlosceronmartinez@icloud.com",
"carson8204@yahoo.com",
"chadcroucher0102@gmail.com",
"chaparromatthew41@mygya.com",
"charliecappin02@gmail.com",
"charlottehorn915@gmail.com",
"chrishubbard0105@gmail.com",
"christian.m.soden@gmail.com",
"chuymap12@gmail.com",
"ckoivu05@gmail.com",
"ckrohlow44@gmail.com",
"clapperl025@gmail.com",
"clarkjsessions6@gmail.com",
"cobiobrien21@gmail.com",
"coleread522@gmail.com",
"colinnewgard@icloud.com",
"colinsaldana444@gmail.com",
"cristianrmz2005@gmail.com",
"culbreathtyreke680@gmail.com",
"cvanvaler@comcast.net",
"damian.r.medina1705@gmail.com",
"danbak2003@yahoo.com",
"darechar8@gmail.com",
"dariuslam04@gmail.com",
"dartwhiteloo@gmail.com",
"datboicam1996@gmail.com",
"dav.per017@gmail.com",
"daveyflo4@gmail.com",
"daveysanch@gmail.com",
"davida4959@gmail.com",
"davidbungardner@gmail.com",
"db041513@gmail.com",
"dbelus1996@gmail.com",
"dblotwitch@gmail.com",
"dbrodnax01@yahoo.com",
"dchavarria039@gmail.com",
"derskin2012@gmail.com",
"dillonrangel1@gmail.com",
"dkenner588@icloud.com",
"dmiller313@icloud.com",
"dmrcswells@gmail.com",
"dominiccalderon578@gmail.com",
"doxphilpott@gmail.com",
"dprince935@gmail.com",
"dweltathlete1@gmail.com",
"e.is.real1216@gmail.com",
"eaton.btandon7@gmail.com",
"ebowles23@icloud.com",
"edwardgwilliams41@gmail.com",
"eggsontoast889@gmail.com",
"eli768483@gmail.com",
"elijah.ghulam@gmail.com",
"elishapichardo1@gmail.com",
"elvelazquez960@icloud.com",
"epachuca414@icloud.com",
"ernestoalain28@gmail.com",
"ezekielluna808@gmail.com",
"flinderscameron@gmail.com",
"floreslx280@gmail.com",
"franciscodelarosa785@gmail.com",
"franklinjones071@gmail.com",
"frankquon13@gmail.com",
"ft100overall23@icloud.com",
"garrettwilliams203@gmail.com",
"garronhanks@gmail.com",
"gavinskyler55@gmail.com",
"glokkeith@gmail.com",
"goddardbraeden80@gmail.com",
"goybailey@gmail.com",
"graceslynnsia@gmail.com",
"harrisfamjt@gmail.com",
"hcarv004@gmail.com",
"hclukey256@gmail.com",
"heathbozworth7@gmail.com",
"heflin.blake.k@gmail.com",
"heflir.blake.k@gmail.com",
"hendrixlawson05@gmail.com",
"henryguts878@gmail.com",
"hiphopsippy@icloud.com",
"hudhayfahal@gmail.com",
"hunterhemphill707@gmail.com",
"hunterhottle52142@gmail.com",
"huntrerobinson762@gmail.com",
"iainmahoney04@gmail.com",
"ihaveacrushonshay@gmail.com",
"ijwhwork@gmail.com",
"indy_5050@icloud.com",
"isaiah.alvarez1223@gmail.com",
"isilelimasi691@gmail.com",
"isnagrsn@yahoo.com",
"ivan.bocanegra1@icloud.com",
"ivanj000@icloud.com",
"jac2281395@maricopa.edu",
"jackkilbride@icloud.com",
"jacqueline.lopezromero@gmail.com",
"jadenday90@gmail.com",
"jadingeorge321@gmail.com",
"jamesj.hour@gmail.com",
"jaredsalinas25@gmail.com",
"jasonweber420@icloud.com",
"jawill0409@gmail.com",
"jctrinchere1@gmail.com",
"jgravestocker@gmail.com",
"jhersongomora0@gmail.com",
"jibransoto21@gmail.com",
"jimmysalasjr2424@yahoo.com",
"jlopezjudo321@gmail.com",
"jonathancano12345678@gmail.com",
"jonathanhickman6969@gmail.com",
"joonhyunga@gmail.com",
"jorgecornejo9999@gmail.com",
"joseguevara.3924@gmail.com",
"joseph.joey.thomas@gmail.com",
"josephgates2005@gmail.com",
"josephmbellardo@gmail.com",
"joshuabarran@gmail.com",
"joshuahunt5595@gmail.com",
"jules@dwellersoul.com",
"julius.kilpatrick@gmail.com",
"junjames74@gmail.com",
"justinwinterling33@gmail.com",
"jwpalmeriii@gmail.com",
"kadenhowe246@gmail.com",
"kadenjames4@gmail.com",
"kallweitnoah1@gmail.com",
"kanemccallan10@gmail.com",
"karmen.aldaco@gmail.com",
"karsonhaysbert@gmail.com",
"kaylalim911@gmail.com",
"kdill490@gmail.com",
"keagan.schnoor@gmail.com",
"kellencohen4@gmail.com",
"kellzhytrek@gmail.com",
"kgubler22@gmail.com",
"kilsins4@gmail.com",
"kimsy0406@yahoo.com",
"konnerbellgeyler@icloud.com",
"kristoferpowell29@gmail.com",
"kylantopp@gmail.com",
"l.forcino12@gmail.com",
"l0gancarpenter@icloud.com",
"lancewilli04@gmail.com",
"lemarionm47@gmail.com",
"leonardomendoza047@gmail.com",
"levifeltes@gmail.com",
"lnini8481@gmail.com",
"lorenzoftw101@gmail.com",
"louhanson681@gmail.con",
"m_gmarcello083@gmail.com",
"macelav11@gmail.com",
"marlicvalentine@gmail.com",
"marron.matte@gmail.com",
"masonrowan926@gmail.com",
"matthewaddison223@gmail.com",
"matthewczipper@gmail.com",
"megan.mcentee@me.com",
"mfeakerqc@yahoo.com",
"michaelbond3209@gmail.com",
"michaelfenner05@outlook.com",
"mipoderes@gmail.com",
"mkl98@ymail.com",
"mochajoeshizzle@icloud.com",
"monroe.mozee@icloud.com",
"msheehan@gowva.org",
"munoz.jeremiahp@gmail.com",
"myrealnameisterrence@gmail.com",
"newbalance641@gmail.com",
"nicholas.cadena0505@gmail.com",
"nicolasagtern@gmail.com",
"olearysean32@gmail.com",
"oliverstudebaker3@gmail.com",
"orionjr.cud@gmail.com",
"paige.michalski@icloud.com",
"patrickdemlax@gmail.com",
"pedroluquin00@gmail.com",
"peeblesbraylon@gmail.com",
"perezgiovanni238@gmail.com",
"pernellsylvester@icloud.com",
"petersonronnie04@gmail.com",
"poppystorm07@gmail.com",
"preston.hatkow@gmail.com",
"qmccornack@gmail.com",
"qxwby5@gmail.com",
"raddaaron@gmail.com",
"ralund@outlook.com",
"rashidahmadzai2030@gmail.com",
"raulrios132@yahoo.com",
"rcontreras100903@gmail.com",
"rdschmollinger@gmail.com",
"ridgelray9@gmail.com",
"robert.chavez511@gmail.com",
"rolanbr4@gmail.com",
"rome.hinojosa@hotmail.con",
"ryguyboyd@gmail.com",
"sabillonsgt1@gmail.com",
"sageriver984@gmail.com",
"salcedojunior720@gmail.com",
"samanthaaugust72@gmail.com",
"samuelalexander132019@outlook.com",
"samuelgauthier2020@gmail.com",
"samuelk6285@gmail.com",
"seanw888willow@gmail.com",
"sebastianmorae02@gmail.com",
"sethkvamme@gmail.com",
"shauntaenight21@gmail.com",
"sherlyngar2006@gmail.com",
"shiloweston97@gmail.com",
"sias.gavin@yahoo.com",
"smonreal678@gmail.com",
"sseas2423@yahoo.com",
"st20078891@gmail.com",
"starrettquarry@icloud.com",
"tanner.caldwell@icloud.com",
"tannerbraun1776@gmail.com",
"tedpierre134@gmail.com",
"test10aa@automation.com",
"test@test.com",
"tgohlke@yahoo.com",
"thomasnthomas3@gmail.com",
"tmp1023@gmail.com",
"tonyfold85@gmail.com",
"tonymontana23z@icloud.com",
"tracymason516@gmail.com",
"trevorbenallie@gmail.com",
"trinidadkeven99@gmail.com",
"tyflo310@gmail.com",
"tyleracrites@gmail.com",
"tyranttypical@gmail.com",
"tyrohlman@gnail.com",
"upshaw3rdkevin@gmail.com",
"urielsantacruz85@gmail.com",
"vanillagorilla249@gmail.com",
"velardezgm@gmail.com",
"villakevn@gmail.com",
"vjsmith579@gmail.com",
"vukujavec@gmail.com",
"waynejohnstonx@gmail.com",
"williamgalloway11@gmail.com",
"yung.jr1011@gmail.com",
"zach.hoydic@yahoo.com",
"zachpt222@gmail.com",
"zbarnes8@icloud.com",
"zepolbur@gmail.com",
"zinfante25@gmail.com",
"carbajalirving8@gmail.com",
"rmullett33@gmail.com",
"giancarlococcia1220@gmail.com",
"elijahjhull@gmail.com",
"cjmags212@gmail.com",
"fg1407840@gmail.com",
"tannerbarker58@gmail.com",
]


# 19justingriffis87@gmail.com
# 24jgasca@gmail.com
# 80ggabriel10@gmail.com
# aasghar747@gmail.com
# agg003@morningside.edu
# aguilariiiesteban@gmail.com
# ahmadaimaq302@gmail.com
# aiden.prows@icloud.com
# aidenmyhre2@gmail.com
# alexisvictoriano@icloud.com
# allan.barrera2006@gmail.com
# am559u1313@gmail.com
# amayaalvaro2@gmail.com
# amsanchez202020@gmail.com
# andrelsouzaca@gmail.com
# andrewostrihon@gmail.com
# andrusethan7@gmail.com
# angelacostaa710@gmail.com
# angelrangeltobro@gmail.com
# anthony.nguyen1002@gmail.com
# antonchacon05@gmail.com
# ap3942281@gmail.com
# ap3ters1904@gmail.com
# archibaldpuddin@gmail.com
# arlobautista21@icloud.com
# arturojaracuaro16@gmail.com
# austin.laskaris@k12csd.us
# aydenprater42@gmail.com
# bDLiS3kvCHUAivkOaSwg
# baldwinamos93@gmail.com
# bengooltz123a@gmail.com
# bennyjc04@gmail.com
# bigm4033@gmail.com
# blk_bam@yahoo.com
# bmax57901@gmail.com
# bootonconner@gmail.com
# bradyfire05@gmail.com
# braidendockins18@gamil.com
# brettbernier123@gmail.com
# browneli007@icloud.com
# brussell3218@icloud.com
# buchs.james@gmail.com
# buddasmain@gmail.com
# burnell.ed@gmail.com
# buttmunch021@gmail.com
# byonrobert@gmail.com
# caison117echols@gmail.com
# camwalt01@yahoo.com
# canulnoe406@gmail.com
# carlosceronmartinez@icloud.com
# carson8204@yahoo.com
# chadcroucher0102@gmail.com
# chaparromatthew41@mygya.com
# charliecappin02@gmail.com
# charlottehorn915@gmail.com
# chrishubbard0105@gmail.com
# christian.m.soden@gmail.com
# chuymap12@gmail.com
# ckoivu05@gmail.com
# ckrohlow44@gmail.com
# clapperl025@gmail.com
# clarkjsessions6@gmail.com
# cobiobrien21@gmail.com
# coleread522@gmail.com
# colinnewgard@icloud.com
# colinsaldana444@gmail.com
# cristianrmz2005@gmail.com
# culbreathtyreke680@gmail.com
# cvanvaler@comcast.net
# damian.r.medina1705@gmail.com
# danbak2003@yahoo.com
# darechar8@gmail.com
# dariuslam04@gmail.com
# dartwhiteloo@gmail.com
# datboicam1996@gmail.com
# dav.per017@gmail.com
# daveyflo4@gmail.com
# daveysanch@gmail.com
# davida4959@gmail.com
# davidbungardner@gmail.com
# db041513@gmail.com
# dbelus1996@gmail.com
# dblotwitch@gmail.com
# dbrodnax01@yahoo.com
# dchavarria039@gmail.com
# derskin2012@gmail.com
# dillonrangel1@gmail.com
# dkenner588@icloud.com
# dmiller313@icloud.com
# dmrcswells@gmail.com
# dominiccalderon578@gmail.com
# doxphilpott@gmail.com
# dprince935@gmail.com
# dweltathlete1@gmail.com
# e.is.real1216@gmail.com
# eaton.btandon7@gmail.com
# ebowles23@icloud.com
# edwardgwilliams41@gmail.com
# eggsontoast889@gmail.com
# eli768483@gmail.com
# elijah.ghulam@gmail.com
# elishapichardo1@gmail.com
# elvelazquez960@icloud.com
# epachuca414@icloud.com
# ernestoalain28@gmail.com
# ezekielluna808@gmail.com
# flinderscameron@gmail.com
# floreslx280@gmail.com
# franciscodelarosa785@gmail.com
# franklinjones071@gmail.com
# frankquon13@gmail.com
# ft100overall23@icloud.com
# garrettwilliams203@gmail.com
# garronhanks@gmail.com
# gavinskyler55@gmail.com
# glokkeith@gmail.com
# goddardbraeden80@gmail.com
# goybailey@gmail.com
# graceslynnsia@gmail.com
# harrisfamjt@gmail.com
# hcarv004@gmail.com
# hclukey256@gmail.com
# heathbozworth7@gmail.com
# heflin.blake.k@gmail.com
# heflir.blake.k@gmail.com
# hendrixlawson05@gmail.com
# henryguts878@gmail.com
# hiphopsippy@icloud.com
# hudhayfahal@gmail.com
# hunterhemphill707@gmail.com
# hunterhottle52142@gmail.com
# huntrerobinson762@gmail.com
# iainmahoney04@gmail.com
# ihaveacrushonshay@gmail.com
# ijwhwork@gmail.com
# indy_5050@icloud.com
# isaiah.alvarez1223@gmail.com
# isilelimasi691@gmail.com
# isnagrsn@yahoo.com
# ivan.bocanegra1@icloud.com
# ivanj000@icloud.com
# jac2281395@maricopa.edu
# jackkilbride@icloud.com
# jacqueline.lopezromero@gmail.com
# jadenday90@gmail.com
# jadingeorge321@gmail.com
# jamesj.hour@gmail.com
# jaredsalinas25@gmail.com
# jasonweber420@icloud.com
# jawill0409@gmail.com
# jctrinchere1@gmail.com
# jgravestocker@gmail.com
# jhersongomora0@gmail.com
# jibransoto21@gmail.com
# jimmysalasjr2424@yahoo.com
# jlopezjudo321@gmail.com
# jonathancano12345678@gmail.com
# jonathanhickman6969@gmail.com
# joonhyunga@gmail.com
# jorgecornejo9999@gmail.com
# joseguevara.3924@gmail.com
# joseph.joey.thomas@gmail.com
# josephgates2005@gmail.com
# josephmbellardo@gmail.com
# joshuabarran@gmail.com
# joshuahunt5595@gmail.com
# jules@dwellersoul.com
# julius.kilpatrick@gmail.com
# junjames74@gmail.com
# justinwinterling33@gmail.com
# jwpalmeriii@gmail.com
# kadenhowe246@gmail.com
# kadenjames4@gmail.com
# kallweitnoah1@gmail.com
# kanemccallan10@gmail.com
# karmen.aldaco@gmail.com
# karsonhaysbert@gmail.com
# kaylalim911@gmail.com
# kdill490@gmail.com
# keagan.schnoor@gmail.com
# kellencohen4@gmail.com
# kellzhytrek@gmail.com
# kgubler22@gmail.com
# kilsins4@gmail.com
# kimsy0406@yahoo.com
# konnerbellgeyler@icloud.com
# kristoferpowell29@gmail.com
# kylantopp@gmail.com
# l.forcino12@gmail.com
# l0gancarpenter@icloud.com
# lancewilli04@gmail.com
# lemarionm47@gmail.com
# leonardomendoza047@gmail.com
# levifeltes@gmail.com
# lnini8481@gmail.com
# lorenzoftw101@gmail.com
# louhanson681@gmail.con
# m_gmarcello083@gmail.com
# macelav11@gmail.com
# marlicvalentine@gmail.com
# marron.matte@gmail.com
# masonrowan926@gmail.com
# matthewaddison223@gmail.com
# matthewczipper@gmail.com
# megan.mcentee@me.com
# mfeakerqc@yahoo.com
# michaelbond3209@gmail.com
# michaelfenner05@outlook.com
# mipoderes@gmail.com
# mkl98@ymail.com
# mochajoeshizzle@icloud.com
# monroe.mozee@icloud.com
# msheehan@gowva.org
# munoz.jeremiahp@gmail.com
# myrealnameisterrence@gmail.com
# newbalance641@gmail.com
# nicholas.cadena0505@gmail.com
# nicolasagtern@gmail.com
# olearysean32@gmail.com
# oliverstudebaker3@gmail.com
# orionjr.cud@gmail.com
# paige.michalski@icloud.com
# patrickdemlax@gmail.com
# pedroluquin00@gmail.com
# peeblesbraylon@gmail.com
# perezgiovanni238@gmail.com
# pernellsylvester@icloud.com
# petersonronnie04@gmail.com
# poppystorm07@gmail.com
# preston.hatkow@gmail.com
# qmccornack@gmail.com
# qxwby5@gmail.com
# raddaaron@gmail.com
# ralund@outlook.com
# rashidahmadzai2030@gmail.com
# raulrios132@yahoo.com
# rcontreras100903@gmail.com
# rdschmollinger@gmail.com
# ridgelray9@gmail.com
# robert.chavez511@gmail.com
# rolanbr4@gmail.com
# rome.hinojosa@hotmail.con
# ryguyboyd@gmail.com
# sabillonsgt1@gmail.com
# sageriver984@gmail.com
# salcedojunior720@gmail.com
# samanthaaugust72@gmail.com
# samuelalexander132019@outlook.com
# samuelgauthier2020@gmail.com
# samuelk6285@gmail.com
# seanw888willow@gmail.com
# sebastianmorae02@gmail.com
# sethkvamme@gmail.com
# shauntaenight21@gmail.com
# sherlyngar2006@gmail.com
# shiloweston97@gmail.com
# sias.gavin@yahoo.com
# smonreal678@gmail.com
# sseas2423@yahoo.com
# st20078891@gmail.com
# starrettquarry@icloud.com
# tanner.caldwell@icloud.com
# tannerbraun1776@gmail.com
# tedpierre134@gmail.com
# test10aa@automation.com
# test@test.com
# tgohlke@yahoo.com
# thomasnthomas3@gmail.com
# tmp1023@gmail.com
# tonyfold85@gmail.com
# tonymontana23z@icloud.com
# tracymason516@gmail.com
# trevorbenallie@gmail.com
# trinidadkeven99@gmail.com
# tyflo310@gmail.com
# tyleracrites@gmail.com
# tyranttypical@gmail.com
# tyrohlman@gnail.com
# upshaw3rdkevin@gmail.com
# urielsantacruz85@gmail.com
# vanillagorilla249@gmail.com
# velardezgm@gmail.com
# villakevn@gmail.com
# vjsmith579@gmail.com
# vukujavec@gmail.com
# waynejohnstonx@gmail.com
# williamgalloway11@gmail.com
# yung.jr1011@gmail.com
# zach.hoydic@yahoo.com
# zachpt222@gmail.com
# zbarnes8@icloud.com
# zepolbur@gmail.com
# zinfante25@gmail.com
# carbajalirving8@gmail.com
# rmullett33@gmail.com
# giancarlococcia1220@gmail.com
# elijahjhull@gmail.com
# cjmags212@gmail.com
# fg1407840@gmail.com
# tannerbarker58@gmail.com