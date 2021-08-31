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
		/// <summary>
		/// The file containing all the profile to update
		/// </summary>
		public const string _updaterFile = "updater.txt";
		public const string _pythonFileToLaunch = "onlyfans-dl.py";
		public const string _subFolderName = "profiles";
		public const char _spliter = ',';
		public const char _slash = '\\';
		public static bool _askBeforeClosing = true;

		private static List<string> _profiles;

		private static string currentFolder;
		private static string subFolder;
		private static string pythonFileFullPath;
		private static string updaterFileFullPath;
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
			
			#region Initialising the variables
			_profiles = new List<string>();
			currentFolder = Directory.GetCurrentDirectory();
			subFolder = currentFolder + _slash + _subFolderName;
			pythonFileFullPath = currentFolder + _slash + _pythonFileToLaunch;
			updaterFileFullPath = currentFolder + _slash + _updaterFile;
			#endregion
			
			//Check if the "profiles" folders exist to get all the already downloaded profile and update them
			if (HasProfileToUpdate(out var profileToUpdate))
			{
				Console.WriteLine("Profiles you might want to update :");
				Console.WriteLine(String.Join($" {_spliter} ",profileToUpdate));
				Console.WriteLine("Do you want to Update them ? (Y/N)");
				if (AskYesOrNo()) AddProfile(profileToUpdate);
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
				string[] answer = ProcessProfiles(answerRaw).Split(_spliter);
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
		
		/// <summary>
		/// Process all the answer that I get to remove the potential whitespace that a user could enter (which are not suppose to exist)
		/// </summary>
		/// <param name="answer">The answer to process</param>
		/// <returns>The answer processed</returns>
		private static string ProcessProfiles(string answer)
		{
			return Regex.Replace(answer, @"\s", String.Empty);
		}
		
		/// <summary>
		/// Process all the answer that I get to remove the potential whitespace that a user could enter (which are not suppose to exist)
		/// </summary>
		/// <param name="answer">The array of answer to process</param>
		private static void ProcessProfiles(string[] answer)
		{
			if (answer == null) return;
			
			for (int i = 0; i < answer.Length; i++)
			{
				//Simple regex to remove any whitespace character.
				answer[i] = Regex.Replace(answer[i], @"\s", String.Empty);
			}
		}

		/// <summary>
		/// Check if we have profile to update, either by a certain text file or using the folder we already created. <br />
		/// In the text files, no matter the whitespace, the profiles must be separate with a comma. (meaning you can put space before and after, or a new line between each)
		/// </summary>
		/// <param name="profileFound"></param>
		/// <returns></returns>
		private static bool HasProfileToUpdate(out string[] profileFound)
		{
			if (File.Exists(updaterFileFullPath))
			{
				profileFound = ProcessProfiles(File.ReadAllText(updaterFileFullPath)).Split(_spliter);
				return true;
			}
			else if (Directory.Exists(subFolder))
			{
				profileFound = Directory.GetDirectories(subFolder);
				for (int i = 0; i < profileFound.Length; i++)
				{
					profileFound[i] = profileFound[i].Split('\\', '/').LastOrDefault();
				}

				return true;
			}

			profileFound = null;
			return false;
		}
		private static bool AskYesOrNo()
		{
			var answer = Console.ReadKey();
			return answer.KeyChar != 'N' && answer.KeyChar != 'n';
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