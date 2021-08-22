using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;

namespace onlyfans_dl_updater
{
	class Updater
	{
		public const string _pythonFileToLaunch = "onlyfans-dl.py";
		public const string _subFolderName = "profiles";
		public const char _spliter = ',';
		public const char _slash = '\\';
		public static bool _askBeforeClosing = true;

		private static List<string> _profiles;
		
		static void Main(params string[] args)
		{
			//First, processing every arguments
			ProcessArguments(args);
			
			//Check if the python file is in the same folder as the .exe
			if (!File.Exists(_pythonFileToLaunch))
			{
				Console.WriteLine($"The file {_pythonFileToLaunch} must be in the same folder as this executable.");
				End();
				return;
			}
			
			//Initialising the variables
			_profiles = new List<string>();
			string currentFolder = Directory.GetCurrentDirectory();
			string subFolder = currentFolder + _slash + _subFolderName;
			string pythonFileFullPath = currentFolder + _slash + _pythonFileToLaunch;
			
			//Check if the "profiles" folders exist to get all the already downloaded profile and update them
			if (Directory.Exists(subFolder))
			{
				var existingProfile = Directory.GetDirectories(subFolder);
				for (int i = 0; i < existingProfile.Length; i++)
				{
					existingProfile[i] = existingProfile[i].Split('\\','/').LastOrDefault();
				}
				
				Console.WriteLine("Currently existing profiles :");
				Console.WriteLine(String.Join($" {_spliter}",existingProfile));
				Console.WriteLine("Do you want to Update them ? (Y/N)");
				var answer = Console.ReadKey();
				if (answer.KeyChar != 'N' && answer.KeyChar != 'n') AddProfile(existingProfile);
				Console.Write("\n");
			}
			
			//Asking the user for more profile if needed (can write many to later download all of them)
			Console.WriteLine($"Write the profiles you want to add et separate them with a <{_spliter}>.");
			Console.WriteLine("Or simply skip this step by writing nothing and pressing enter.");
			Console.Write("\n");
			string answerRaw = Console.ReadLine();
			
			//If there is an answer we process it and add it to the profiles to download
			if (!String.IsNullOrEmpty(answerRaw))
			{
				string[] answer = answerRaw.Split(_spliter);
				ProcessAnswer(answer);
				AddProfile(answer);
			}

			//if there is no profile in the list, we stop here.
			if (_profiles.Count == 0)
			{
				Console.WriteLine("No profiles you want to update, that's fine, we'll stop there. See you soon !");
				End();
				return;
			}
			
			string baseCmdCommand = $"/C python {pythonFileFullPath}";

			//We'll start a command for every profile we got one after the other
			foreach (var profile in _profiles)
			{
				string cmdCommand = $"{baseCmdCommand} \"{profile}\"";
				AnnounceCommand(cmdCommand);
				var process = Process.Start("CMD.exe",cmdCommand);
				process.WaitForExit();
			}
			Announce();
			
			End();
		}
		
		//processing the arguments in case there is any
		//(currently there is only "dontAskToClose" but not even sure if it will ever be use)
		private static void ProcessArguments(string[] args)
		{
			_askBeforeClosing = !args.Any(arg => arg.Equals("dontAskToClose", StringComparison.CurrentCultureIgnoreCase));
		}

		//Function that I use to not immediately end the program but ask for an input before the user
		private static void End()
		{
			if (!_askBeforeClosing) return;
			Console.Write("\nPress any key to end. ");
			Console.ReadKey();
		}

		//Add a list of profile by always checking that the profile don't already exist.
		private static void AddProfile(string[] profiles)
		{
			foreach (var profile in profiles)
			{
				if (!_profiles.Contains(profile))
				{
					_profiles.Add(profile);
				}
			}
		}

		//Announce anything that I need, or just do a separation
		private static void Announce(string text = "")
		{
			string seperator = "=========================================";
			Console.WriteLine(seperator);
			if (String.IsNullOrEmpty(text)) return;
			Console.WriteLine(text);
			Console.WriteLine(seperator);
		}

		//Announce a command that I launch (also serv as a separator)
		private static void AnnounceCommand(string command)
		{
			char newLine = '\n';
			string text = $"Starting <{command}>";
			string seperator = new String('=',text.Length);
			Console.WriteLine(newLine+seperator);
			Console.WriteLine(text);
			Console.WriteLine(seperator+newLine);
		}

		//Process all the answer that I get to remove the potential whitespace that a user could enter (which are not suppose to exist)
		private static void ProcessAnswer(string[] answer)
		{
			if (answer == null) return;
			
			for (int i = 0; i < answer.Length; i++)
			{
				//Simple regex to remove any whitespace character.
				answer[i] = Regex.Replace(answer[i], @"\s", String.Empty);
			}
		}
		
		//Debug an entire array, in case I need it
		private static void Debug<T>(T[] array)
		{
			if (array == null) return;
			Console.WriteLine($"Array of type {typeof(T).Name} of {array.Length} elements :");
			for (int i = 0; i < array.Length; i++)
			{
				Console.WriteLine($"{i}: {array[i].ToString()}");
			}
		}
	}
}