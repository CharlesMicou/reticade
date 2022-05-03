% I've hacked this together from the existing Krupic scripts to mass-
% extract position data. It's hideous and I take no responsibility for
% the nonsense that follows.


clearvars;
GAVLO_THRESH = 0.1; % EDITME
frame_averaging = 2; % EDITME
pos_file = '<>_pos.bin'; % EDITME
adat_file = '<>_adat.bin'; % EDITME

fsz = dir(adat_file);
fr_size = 16 + 4 + 4 + 1000*8; % timestamp(16bytes) + LV timer (4 bytes) + length of data frame (4 bytes, always equal to 1000) + 1000 x galvo data (8 bytes)
kiek_frames = fsz.bytes/fr_size; % how many frames in the file

galvoo = zeros(1,kiek_frames*1000); % variable for galvo signal
galvoo_time = zeros(1,kiek_frames*1000);
fileDAT = fopen(adat_file);

for i = 1:kiek_frames
    % The first 8 bytes represent seconds since 1/1/1904 midnight GMT.  The second 8 bytes is a 2^64 bit fraction of a second.
    t_st1(i) = fread(fileDAT,1,'*uint64','ieee-be');
    t_st2(i) = fread(fileDAT,1,'*uint64','ieee-be');
    adat_tim(i) = fread(fileDAT,1,'*uint32','ieee-be');
    t_bs(i) = fread(fileDAT,1,'*uint32','ieee-be');
    t_dat = fread(fileDAT,1000,'*double','ieee-be')'; 
    galvoo(((i-1)*1000+1):((i-1)*1000+1000)) = t_dat;
    galvoo_time(((i-1)*1000+1):((i-1)*1000+1000)) = adat_tim(i):(adat_tim(i)+999);
end
fclose(fileDAT)


fsz = dir(pos_file);
fileID = fopen(pos_file);


fr_size = 11*8; % 11 doubles
kiek_frames = fsz.bytes/fr_size; % how many frames in the file

rbsh = zeros(5,kiek_frames);

for i = 1:kiek_frames         
    pos_tim(i) = fread(fileID,1,'*double','ieee-be');
    pos_pos(i) = fread(fileID,1,'*double','ieee-be');
    pos_thr(i) = fread(fileID,1,'*double','ieee-be');
    pos_direc(i) = fread(fileID,1,'*double','ieee-be');
    pos_val(i) = fread(fileID,1,'*double','ieee-be');    
    pos_fou(i) = fread(fileID,1,'*double','ieee-be');
    rbsh(:,i) = fread(fileID,5,'*double','ieee-be');
end
    
fclose(fileID)

pos_tim_t = pos_tim - pos_tim(1);

% INTERPOLATION 
% added on 070619: extremely important!!! without this
% interpolation step we had a mismatch between position and spikes (drift
% problem...)

i_pos_x = interp1(pos_tim_t,pos_pos,1:20:max(pos_tim_t));
i_tim_t = 1:20:max(pos_tim_t);

pos_tim_interp = i_tim_t + pos_tim(1);


% positions sampled at 50hz, adat sampled at 1000Hz

% align the pos and dat
% 1. get the galvo time
% 2. find the average position in the galvo frame

%% describe and extract trial data here
% find and group trials
gg=galvoo; gg(gg<-1)=0; % to remove initialization
aa=[0 diff(galvoo)];
aa(aa<0.3)=0; % threshold diff(galvoo)

% aa(2)=1;
[~,locs] = findpeaks(aa); % find the frames
locs = [locs length(aa)];

ee = [(diff(locs)) 0];
eee = ee;
ee(ee<1e4)=0; % trial separation below 10 seconds = 0
eee(eee>5e3)=0; % frame rate above 5 seconds = 0

% bruteforce method to group into trials
starts = [locs(1)]; % first location shows that the trial started
ends = [];
which_trial = 1;
tt_numeriukas = 1;
for tt = 2:length(locs)-1
    if locs(tt+1)-locs(tt) < 3000 % is the difference less than 3 seconds
        continue
    else
        ends(which_trial) = locs(tt);
        frqq(which_trial) = mean(diff(locs(tt_numeriukas:tt)));
        freimu_skaicius(which_trial) = tt-tt_numeriukas;
        tt_numeriukas = tt+1;        
        which_trial = which_trial + 1;
        starts(which_trial) = locs(tt+1);
    end    
end
starts=starts(1:end-1);

% remove too short (30 frames) 
pradzios = starts(ends-starts>10000);
pabaigos = ends(ends-starts>10000);
frqq = frqq(ends-starts>10000);
freimu_skaicius = freimu_skaicius(ends-starts>10000);
frqq = 1000./frqq;
% plots and create trial descriptions for choosing
figure(111)
clf
hold on
for oo = 1:length(pradzios)
    plot(pradzios(oo):pabaigos(oo),aa(pradzios(oo):pabaigos(oo)))
    text(0.5*(pradzios(oo)+pabaigos(oo)),1.6,num2str(oo))    
end


disp('-------------------')
disp('choose the correct trials')
disp('sampling frequencies for each trial and a number of frames within a trial')
fprintf('  ')
fprintf('%6d    |   ',1:length(frqq))
fprintf('  \n  ')
fprintf('%6.2f Hz |   ',(frqq))
fprintf('  \n  ')
fprintf('%6d    |   ',(freimu_skaicius))
fprintf('  \n')


keyboard

good_trials = [3 4 5 6];


trial_starts = [pradzios(good_trials)];
trial_ends = [pabaigos(good_trials)];




for ii = 1:length(good_trials)

    % 1. get galvo frames. when galvo starts, it goes -0.8 to 0.7
    galvoo_piece = galvoo(trial_starts(ii):trial_ends(ii));
    galvoo_piece(galvoo_piece>0.8) = -1; % seems that in resonant mode the resting V is >1V

    %[hgh, kur_frames] = findpeaks(galvoo_piece,'MinPeakHeight',0.6,'MinPeakDistance',30);
    

    [hgh, kur_frames] = findpeaks(galvoo_piece,'MinPeakHeight',GAVLO_THRESH,'MinPeakDistance',30);
    
    frams(ii) = length(hgh);
    fram_poses(ii,1:length(hgh)) = kur_frames;
    laikiukai = galvoo_time(trial_starts(ii):trial_ends(ii));
    timsai(ii,1:length(hgh)) = laikiukai(kur_frames);
    
    figure
    plot(galvoo_piece)
    hold on
    %added by PK on 161021
    title(num2str(good_trials(ii)));
    %
    plot(kur_frames,hgh,'or')
    mean_frame_length = round(mean(diff(kur_frames)));
    drawnow()
   
    for j = 1:length(kur_frames)
        time1 = galvoo_time(kur_frames(j)+trial_starts(ii));
        if j < length(kur_frames)
            time2 = galvoo_time(kur_frames(j)+mean_frame_length+trial_starts(ii));
        else
            %         time2 = galvoo_time(end);
            disp('finito')
        end
        
        fr_start = find(abs(pos_tim_interp-time1)==min(abs(pos_tim_interp-time1)),1);
        fr_end = find(abs(pos_tim_interp-time2)==min(abs(pos_tim_interp-time2)),1);
        
        mean_pos(j) = mean(i_pos_x(fr_start:fr_end)); % this shows the average position within the frame
    end
   
    
    mean_pozicijos{ii} = mean_pos;
    
end

trial_frames = [8824 8824 8824 8824];


tf=cumsum(trial_frames);

%unroll positions
mean_pos1 = mean_pozicijos{1};
mean_pos2 = mean_pozicijos{2};
mean_pos3 = mean_pozicijos{3};
mean_pos4 = mean_pozicijos{4};

mean_posb1=[];
mean_posb2=[];
mean_posb3=[];
mean_posb4=[];
if frame_averaging == 1
    mean_posb1 = mean_pos1;
    mean_posb2 = mean_pos2;
    mean_posb3 = mean_pos3;
    mean_posb4 = mean_pos4;
else
    for jj = 1:floor(length(mean_pos1)/frame_averaging)
        mean_posb1(jj) = mean(mean_pos1(((jj-1)*frame_averaging+1):((jj)*frame_averaging)));        
    end
    for jj = 1:floor(length(mean_pos2)/frame_averaging)
        mean_posb2(jj) = mean(mean_pos2(((jj-1)*frame_averaging+1):((jj)*frame_averaging)));        
    end
    for jj = 1:floor(length(mean_pos3)/frame_averaging)
        mean_posb3(jj) = mean(mean_pos3(((jj-1)*frame_averaging+1):((jj)*frame_averaging)));        
    end
    for jj = 1:floor(length(mean_pos4)/frame_averaging)
        mean_posb4(jj) = mean(mean_pos4(((jj-1)*frame_averaging+1):((jj)*frame_averaging)));        
    end
end


try
    pos1=mean_posb1(1:trial_frames(1));
    pos2=mean_posb2(1:trial_frames(2));
    pos3=mean_posb3(1:trial_frames(3));
    pos4=mean_posb4(1:trial_frames(4));
catch
    disp('Could not truncate')
    keyboard
end

writematrix(pos1, 'pos_trial_1.csv')
writematrix(pos2, 'pos_trial_2.csv')
writematrix(pos3, 'pos_trial_3.csv')
writematrix(pos4, 'pos_trial_4.csv')



figure;
plot(mean_pozicijos{1});
ylim([0,900]);
title('position trace on trial 1');

